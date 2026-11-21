from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.models import AuditLog
from core.roles import R
from core.serializers import LabeledModelSerializer

from .models import User


class UserSerializer(LabeledModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        exclude = ["groups", "user_permissions"]
        read_only_fields = ["last_login", "date_joined", "last_seen", "is_superuser"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = instance.display_name
        data["role_display"] = instance.get_role_display()
        return data

    def validate_role(self, value):
        req = self.context.get("request")
        if value == R.SUPER_ADMIN and req and not (req.user.is_superuser or req.user.role == R.SUPER_ADMIN):
            raise serializers.ValidationError("Only a super admin can create another super admin.")
        return value

    def create(self, validated):
        pwd = validated.pop("password", None) or None
        user = User(**validated)
        if pwd:
            user.set_password(pwd)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated):
        pwd = validated.pop("password", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance


class AuditLogSerializer(LabeledModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


def user_payload(user, request=None):
    """The current-user object returned at login and by /auth/me/."""
    photo = None
    if user.photo:
        photo = request.build_absolute_uri(user.photo.url) if request else user.photo.url
    data = {
        "id": user.id, "username": user.username, "email": user.email,
        "first_name": user.first_name, "last_name": user.last_name, "full_name": user.display_name,
        "role": user.role, "role_display": user.get_role_display(), "phone": user.phone,
        "whatsapp": user.whatsapp, "gender": user.gender, "cnic": user.cnic,
        "date_of_birth": user.date_of_birth, "father_name": user.father_name,
        "address": user.address, "city": user.city, "name_arabic": user.name_arabic,
        "photo": photo, "must_change_password": user.must_change_password,
        "is_staff_member": user.is_staff_member, "is_superuser": user.is_superuser,
    }
    sp = getattr(user, "student_profile", None)
    if sp:
        data["student"] = {"id": sp.id, "admission_no": sp.admission_no, "section": str(sp.section) if sp.section else None,
                           "section_id": sp.section_id, "status": sp.status}
    ep = getattr(user, "employee_profile", None)
    if ep:
        data["employee"] = {"id": ep.id, "employee_no": ep.employee_no, "designation": ep.designation}
    if user.role == R.PARENT:
        from core.scopes import children_qs
        data["children"] = [{"id": s.id, "user_id": s.user_id, "name": s.user.display_name, "admission_no": s.admission_no,
                             "section": str(s.section) if s.section else None}
                            for s in children_qs(user).select_related("user", "section")]
    return data


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = user_payload(self.user, self.context.get("request"))
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=["last_seen"])
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


SELF_EDITABLE = ["first_name", "last_name", "email", "phone", "whatsapp", "address", "city", "name_arabic", "photo"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = SELF_EDITABLE
