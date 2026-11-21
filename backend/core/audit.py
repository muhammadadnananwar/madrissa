import decimal

from .models import AuditLog


def client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return (fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")) or None


def _jsonable(v):
    if isinstance(v, decimal.Decimal):
        return str(v)
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def audit(request, action, obj, resource="", changes=None):
    """Write an audit-trail entry. Never raises."""
    try:
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            resource=resource or obj._meta.model_name,
            object_id=str(getattr(obj, "pk", "") or ""),
            object_repr=str(obj)[:255],
            changes={k: _jsonable(v) for k, v in (changes or {}).items()},
            ip_address=client_ip(request),
        )
    except Exception:
        pass
