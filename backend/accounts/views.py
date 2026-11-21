import secrets

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.audit import audit
from core.models import AuditLog
from core.roles import ADMINS, FRONT_DESK, HR, STAFF_ROLES
from core.viewsets import BaseModelViewSet

from .models import User
from .serializers import (AuditLogSerializer, ChangePasswordSerializer, LoginSerializer, PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer, ProfileSerializer, UserSerializer, user_payload)


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    resource_key = "users"
    read_roles = HR + FRONT_DESK
    write_roles = HR
    search_fields = ["username", "first_name", "last_name", "email", "phone", "cnic"]
    filterset_fields = ["role", "is_active", "gender", "city"]
    label, group, icon = "User Accounts", "Administration", "users"
    list_fields = ["username", "first_name", "last_name", "role", "phone", "is_active"]
    ui_actions = [
        {"name": "reset_password", "label": "Reset password", "confirm": "Generate a new temporary password?", "roles": HR},
        {"name": "toggle_active", "label": "Activate / Deactivate", "confirm": "Change account status?", "roles": HR},
    ]

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new = request.data.get("password") or secrets.token_urlsafe(8)
        user.set_password(new)
        user.must_change_password = True
        user.save()
        audit(request, "reset_password", user, "users")
        return Response({"detail": "Password reset.", "temporary_password": new})

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({"detail": "You cannot deactivate yourself."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        audit(request, "toggle_active", user, "users", {"is_active": user.is_active})
        return Response({"detail": f"User {'activated' if user.is_active else 'deactivated'}.", "is_active": user.is_active})


class AuditLogViewSet(BaseModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    resource_key = "audit-logs"
    read_roles = ADMINS
    read_only = True
    search_fields = ["object_repr", "resource", "action", "user__username"]
    filterset_fields = ["action", "resource", "user"]
    label, group, icon = "Audit Trail", "Administration", "shield"
    list_fields = ["timestamp", "user", "action", "resource", "object_repr", "ip_address"]


# ---------------------------------------------------------------- auth views
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except TokenError:
            pass
        return Response({"detail": "Logged out."})


class MeView(APIView):
    def get(self, request):
        request.user.last_seen = timezone.now()
        request.user.save(update_fields=["last_seen"])
        return Response(user_payload(request.user, request))

    def patch(self, request):
        s = ProfileSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        audit(request, "update_profile", request.user, "users")
        return Response(user_payload(request.user, request))


class ChangePasswordView(APIView):
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(s.validated_data["old_password"]):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        audit(request, "change_password", user, "users")
        return Response({"detail": "Password changed."})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_forms"

    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=s.validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail("Password reset", f"Assalamu alaikum {user.display_name},\n\nReset your password: {link}\n",
                      settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return Response({"detail": "If the email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(s.validated_data["uid"])))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, s.validated_data["token"]):
            return Response({"detail": "Link expired or invalid."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return Response({"detail": "Password updated. You can now log in."})


class DirectoryView(APIView):
    """Lightweight staff directory."""

    def get(self, request):
        q = request.query_params.get("q", "")
        qs = User.objects.filter(is_active=True, role__in=STAFF_ROLES)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q))
        show_phone = request.user.is_staff_member
        return Response([{"id": u.id, "name": u.display_name, "role": u.get_role_display(), "phone": u.phone if show_phone else ""}
                         for u in qs.order_by("first_name")[:200]])
