from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .metadata import describe_viewset
from .roles import ACADEMIC, ADMINS, FINANCE, HOSTEL, HR, LIBRARY, R, STUDENT_VIEWERS, Role, has_role, is_admin
from .viewsets import REGISTRY

# Menu groups in display order
GROUP_ORDER = ["Academics", "People & Records", "Admissions", "Attendance", "Leaves", "Learning (LMS)", "Quran Programs",
               "Examinations", "Finance & Accounts", "HR & Payroll", "Library", "Hostel", "Transport",
               "Inventory & Assets", "Communication", "Front Desk", "Dar-ul-Ifta", "Personal Records", "Website CMS",
               "Administration"]


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok", "time": timezone.now()})


class MetaView(APIView):
    """Menu of generic resources the current user can open."""

    def get(self, request):
        user = request.user
        groups = {}
        for key, vs in REGISTRY.items():
            if vs.in_menu(user):
                label = vs.label or vs.queryset.model._meta.verbose_name_plural.title()
                groups.setdefault(vs.group, []).append({"key": key, "label": label, "icon": vs.icon})
        ordered = sorted(groups.items(), key=lambda kv: GROUP_ORDER.index(kv[0]) if kv[0] in GROUP_ORDER else 99)
        return Response({"groups": [{"group": g, "items": sorted(items, key=lambda i: i["label"])} for g, items in ordered],
                         "roles": [{"value": v, "label": l} for v, l in Role.choices]})


class ResourceMetaView(APIView):
    """Field definitions, permissions and actions for one resource."""

    def get(self, request, key):
        vs = REGISTRY.get(key)
        if not vs:
            raise Http404
        if not vs.can_list(request.user):
            raise PermissionDenied()
        return Response(describe_viewset(vs, request.user))


class OptionsView(APIView):
    """id/label pairs for select boxes: /api/options/<key>/?q=&ids=1,2"""

    def get(self, request, key):
        vs = REGISTRY.get(key)
        if not vs:
            raise Http404
        user = request.user
        view = vs()
        view.request, view.format_kwarg, view.kwargs, view.action = request, None, {}, "list"
        if vs.can_list(user):
            qs = view.get_queryset()
        elif user.is_staff_member:
            qs = view.base_queryset()  # labels only, needed for forms
        else:
            raise PermissionDenied()
        ids = request.query_params.get("ids")
        if ids:
            qs = qs.filter(pk__in=[i for i in ids.split(",") if i.isdigit()])
        q = request.query_params.get("q")
        if q and getattr(vs, "search_fields", None):
            cond = Q()
            for f in vs.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        for k, v in request.query_params.items():
            if k in (vs.filterset_fields or []) and v != "":
                qs = qs.filter(**{k: v})
        return Response([{"id": o.pk, "label": str(o)} for o in qs[: int(request.query_params.get("limit", 50))]])


class SearchView(APIView):
    """Global search for people across the institution."""

    def get(self, request):
        from accounts.models import User
        q = request.query_params.get("q", "").strip()
        user = request.user
        if len(q) < 2 or not user.is_staff_member:
            return Response([])
        qs = User.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) |
                                 Q(cnic__icontains=q) | Q(phone__icontains=q) | Q(student_profile__admission_no__icontains=q) |
                                 Q(employee_profile__employee_no__icontains=q)).distinct()
        if not has_role(user, STUDENT_VIEWERS + HR):
            from .scopes import visible_user_ids
            qs = qs.filter(id__in=visible_user_ids(user))
        return Response([{"id": u.id, "name": u.display_name, "role": u.get_role_display(),
                          "extra": getattr(getattr(u, "student_profile", None), "admission_no", None)
                          or getattr(getattr(u, "employee_profile", None), "designation", "")} for u in qs[:20]])


class DashboardView(APIView):
    def get(self, request):
        from .dashboard import build_dashboard
        return Response(build_dashboard(request))
