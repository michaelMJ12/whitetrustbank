from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Balance, LiveTransactionStatus, Notification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_defaults(sender, instance, created, **kwargs):
    """Every new customer gets a zeroed Balance, a resting LiveTransactionStatus, and a welcome notification."""
    if not created or instance.role != "customer":
        return

    Balance.objects.get_or_create(
        user=instance,
        defaults={
            "checking": 0,
            "savings": 0,
            "fixed_amount": 0,
            "fixed_rate": 8.5,
            "fixed_maturity": timezone.now().date() + timedelta(days=548),  # ~18 months
            "fixed_term_months": 18,
        },
    )
    LiveTransactionStatus.objects.get_or_create(user=instance, defaults={"status": "completed"})
    Notification.objects.create(
        user=instance,
        audience=Notification.Audience.CUSTOMER,
        title="Welcome to White Trust Bank",
        body="Your account is ready. Open a fixed deposit or try a transfer to see the live monitor in action.",
        tone="teal",
    )
