from django.db.models import Q

from .models import Notification


def notification_counts(request):
    """Injects `unread_notifications` so the bell badge renders correctly on first paint, before JS polling kicks in."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    if user.role == "admin":
        count = Notification.objects.filter(audience=Notification.Audience.ADMIN, read=False).count()
    else:
        count = Notification.objects.filter(Q(user=user), audience=Notification.Audience.CUSTOMER, read=False).count()
    return {"unread_notifications": count}
