"""
Base ModelViewSet shared by all apps.

Each app declares explicit serializers and viewsets in its own ``serializers.py`` /
``views.py``; this base class only adds the cross-cutting behaviour:
role permissions, row scoping, audit logging, CSV export and the metadata the
portal uses to build menus and forms.
"""
import csv

from django.db import models
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from .audit import audit
from .permissions import RolePermission
from .roles import ALL, has_role, is_admin
from .serializers import AUTO_USER_FIELDS

REGISTRY = {}    # resource_key -> viewset class (filled automatically)
MODEL_KEYS = {}  # model -> resource_key


def _roles(r):
    if r == ALL:
        return {ALL}
    return set(r or ())


def filterable_fields(model):
    out = []
    for f in model._meta.get_fields():
        if not getattr(f, "concrete", False) or f.many_to_many:
            continue
        if isinstance(f, (models.FileField, models.JSONField, models.TextField)):
            continue
        out.append(f.name)
    return out


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [RolePermission]
    ordering_fields = "__all__"

    # --- access control (override per viewset) -----------------------------
    resource_key = None     # URL prefix + key used by the portal
    read_roles = ()         # roles that see all rows
    write_roles = ()        # roles that create/update/delete
    create_roles = ()       # roles that may only create
    scope = None            # staticmethod(qs, user) -> qs for everyone else
    owner_field = None      # FK to User auto-filled with request.user
    owner_edit = False      # True / callable(obj, user): owners may edit
    read_only = False
    ui_actions = []         # @action config: [{name, label, roles, input, confirm, style, row}]

    # --- portal metadata ----------------------------------------------------
    label = None
    group = "General"
    icon = "table"
    list_fields = None
    extra_fields = []       # virtual form fields (e.g. login details for a student)
    menu = True
    menu_roles = None
    description = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("resource_key"):
            return
        model = cls.queryset.model
        if "filterset_fields" not in cls.__dict__:
            cls.filterset_fields = filterable_fields(model)
        if "ordering" not in cls.__dict__:
            cls.ordering = list(model._meta.ordering or ["-pk"])
        if cls.read_only:
            cls.http_method_names = ["get", "head", "options"]
        REGISTRY[cls.resource_key] = cls
        MODEL_KEYS.setdefault(model, cls.resource_key)

    # --- permission helpers (classmethods so metadata can use them) ----------
    @classmethod
    def can_read_all(cls, user):
        return is_admin(user) or has_role(user, _roles(cls.read_roles))

    @classmethod
    def can_write(cls, user):
        return not cls.read_only and (is_admin(user) or has_role(user, _roles(cls.write_roles)))

    @classmethod
    def can_create(cls, user):
        return not cls.read_only and (cls.can_write(user) or (bool(cls.create_roles) and has_role(user, _roles(cls.create_roles))))

    @classmethod
    def can_list(cls, user):
        return cls.can_read_all(user) or cls.can_write(user) or cls.scope is not None or cls.can_create(user)

    @classmethod
    def roles_for_action(cls, name):
        for a in cls.ui_actions:
            if a["name"] == name:
                return _roles(a.get("roles", cls.write_roles))
        return _roles(cls.write_roles)

    @classmethod
    def in_menu(cls, user):
        if not cls.menu:
            return False
        if is_admin(user):
            return True
        if cls.menu_roles is not None:
            return has_role(user, _roles(cls.menu_roles))
        if ALL in _roles(cls.read_roles):
            return cls.can_write(user)
        return cls.can_list(user)

    def is_owner(self, obj, user):
        return bool(self.owner_field) and getattr(obj, f"{self.owner_field}_id", None) == user.id

    # --- queryset -------------------------------------------------------------
    def base_queryset(self):
        qs = super().get_queryset()
        fks = [f.name for f in qs.model._meta.concrete_fields if f.is_relation]
        return qs.select_related(*fks) if fks else qs

    def get_queryset(self):
        qs = self.base_queryset()
        user = self.request.user
        if self.can_read_all(user):
            return qs
        if self.scope is not None:
            return type(self).scope(qs, user)
        if self.can_write(user) or self.can_create(user):
            return qs
        return qs.none()

    # --- write hooks -------------------------------------------------------------
    def perform_create(self, serializer):
        user = self.request.user
        names = {f.name for f in serializer.Meta.model._meta.concrete_fields}
        extra = {f: user for f in AUTO_USER_FIELDS if f in names}
        if self.owner_field and (not self.can_write(user) or not serializer.validated_data.get(self.owner_field)):
            extra[self.owner_field] = user
        self.validate_create(serializer, extra)
        obj = serializer.save(**extra)
        audit(self.request, "create", obj, self.resource_key, serializer.validated_data)
        self.after_save(obj, created=True)

    def perform_update(self, serializer):
        obj = serializer.save()
        audit(self.request, "update", obj, self.resource_key, serializer.validated_data)
        self.after_save(obj, created=False)

    def perform_destroy(self, instance):
        audit(self.request, "delete", instance, self.resource_key)
        instance.delete()

    def validate_create(self, serializer, extra):
        """Hook: raise ValidationError / PermissionDenied, or add to ``extra``."""

    def after_save(self, obj, created):
        """Hook: notifications, side effects."""

    # --- CSV export ------------------------------------------------------------------
    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_queryset())[:20000]
        fields = list(qs.model._meta.concrete_fields)
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{self.resource_key}.csv"'
        writer = csv.writer(resp)
        writer.writerow([str(f.verbose_name).title() for f in fields])
        for obj in qs:
            row = []
            for f in fields:
                if f.is_relation:
                    row.append(str(getattr(obj, f.name) or ""))
                elif f.choices:
                    row.append(getattr(obj, f"get_{f.name}_display")())
                else:
                    row.append(getattr(obj, f.attname))
            writer.writerow(row)
        audit(request, "export", qs.model(), self.resource_key)
        return resp
