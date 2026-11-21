"""In-app notifications used by every app."""
from .models import Notification


def notify(users, title, body="", link="", kind="info"):
    """Create in-app notifications for one or many users."""
    if users is None:
        return
    if hasattr(users, "pk"):
        users = [users]
    Notification.objects.bulk_create([
        Notification(user=u, title=title[:200], body=body, link=link, kind=kind) for u in users if u is not None
    ])
