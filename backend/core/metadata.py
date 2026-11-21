"""Describe viewsets/models so the portal can render menus, tables and forms."""
from django.db import models

from .audit import _jsonable
from .roles import has_role, is_admin
from .serializers import AUTO_USER_FIELDS
from .viewsets import MODEL_KEYS


def describe_field(f, readonly_names):
    d = {
        "name": f.name,
        "label": str(f.verbose_name)[:1].upper() + str(f.verbose_name)[1:],
        "help": str(f.help_text or ""),
        "required": (not f.blank) if f.many_to_many else not (f.blank or f.null or f.has_default()),
        "nullable": bool(f.null),
        "readonly": (
            f.name in readonly_names or f.name in AUTO_USER_FIELDS or f.name in ("created_at", "updated_at")
            or getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False) or not f.editable
        ),
    }
    if f.choices and not f.is_relation:
        d["type"] = "choice"
        d["choices"] = [{"value": v, "label": str(lbl)} for v, lbl in f.flatchoices]
    elif f.many_to_many:
        d["type"], d["resource"] = "m2m", MODEL_KEYS.get(f.related_model)
    elif f.is_relation:
        d["type"], d["resource"] = "fk", MODEL_KEYS.get(f.related_model)
    elif isinstance(f, models.ImageField):
        d["type"] = "image"
    elif isinstance(f, models.FileField):
        d["type"] = "file"
    elif isinstance(f, models.EmailField):
        d["type"] = "email"
    elif isinstance(f, models.URLField):
        d["type"] = "url"
    elif isinstance(f, models.TextField):
        d["type"] = "text"
    elif isinstance(f, models.BooleanField):
        d["type"] = "boolean"
    elif isinstance(f, models.DateTimeField):
        d["type"] = "datetime"
    elif isinstance(f, models.DateField):
        d["type"] = "date"
    elif isinstance(f, models.TimeField):
        d["type"] = "time"
    elif isinstance(f, (models.DecimalField, models.FloatField)):
        d["type"] = "decimal"
    elif isinstance(f, models.IntegerField):
        d["type"] = "integer"
    elif isinstance(f, models.JSONField):
        d["type"] = "json"
    else:
        d["type"] = "string"
    if f.has_default() and not callable(f.default) and not f.is_relation:
        d["default"] = _jsonable(f.default)
    return d


def describe_viewset(vs, user):
    model = vs.queryset.model
    smeta = getattr(vs.serializer_class, "Meta", None)
    exclude = set(getattr(smeta, "exclude", None) or ())
    readonly = set(getattr(smeta, "read_only_fields", None) or ())
    fields = []
    for f in model._meta.get_fields():
        if not getattr(f, "concrete", False) or f.primary_key or f.name in exclude:
            continue
        fields.append(describe_field(f, readonly))
    if vs.extra_fields:  # profile + login are created together: the raw `user` link is set by the server
        for fd in fields:
            if fd["name"] == "user":
                fd["required"], fd["hidden"] = False, True
    extra_names = {e["name"] for e in vs.extra_fields}
    fields = [dict(e, extra=True) for e in vs.extra_fields] + [fd for fd in fields if fd["name"] not in extra_names]
    if vs.owner_field and not vs.can_write(user):
        for fd in fields:
            if fd["name"] == vs.owner_field:
                fd["readonly"] = fd["hidden"] = True
    list_fields = vs.list_fields or [fd["name"] for fd in fields if fd["type"] not in ("text", "json", "m2m", "file", "image")][:6]
    actions = [{k: v for k, v in a.items() if k != "roles"} for a in vs.ui_actions
               if is_admin(user) or has_role(user, vs.roles_for_action(a["name"]))]
    editable = vs.can_write(user) or (bool(vs.owner_edit) and not vs.read_only)
    return {
        "key": vs.resource_key,
        "label": vs.label or model._meta.verbose_name_plural.title(),
        "singular": str(model._meta.verbose_name).title(),
        "group": vs.group,
        "icon": vs.icon,
        "description": vs.description,
        "fields": fields,
        "list_fields": list_fields,
        "search": bool(getattr(vs, "search_fields", None)),
        "can_create": vs.can_create(user),
        "can_edit": editable,
        "can_delete": editable,
        "actions": actions,
    }
