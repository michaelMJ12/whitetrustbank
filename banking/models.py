import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

# ---------------------------------------------------------------------------
# Shared vocabulary. Kept in one place so the models, the admin control API,
# and the frontend colour-coding (banking/api.py exposes this as JSON via
# GET /api/meta/) all agree on the same category list.
# ---------------------------------------------------------------------------
CATEGORY_META = {
    "internal":   {"label": "Internal transfer",     "color": "#0F5C4E"},
    "withdrawal": {"label": "Withdrawal",             "color": "#C9A227"},
    "deposit":    {"label": "Deposit",                "color": "#2A6F97"},
    "bill":       {"label": "Bill payment",           "color": "#6B4C9A"},
    "external":   {"label": "External / interbank",   "color": "#B34766"},
    "card":       {"label": "Card purchase",          "color": "#17836F"},
    "admin":      {"label": "Credit Adjustment",       "color": "#5B6472"},
}
CATEGORY_CHOICES = [(key, meta["label"]) for key, meta in CATEGORY_META.items()]

# stage number + tone (colour family) per live-status value. tone drives the
# heartbeat animation speed/colour on the frontend (see static/js/app.js).
STAGE_META = {
    "processing":   {"stage": 1, "label": "Transaction submitted",     "tone": "teal"},
    "network":      {"stage": 2, "label": "Checking network route",    "tone": "teal"},
    "verification": {"stage": 3, "label": "Verifying with issuer",     "tone": "gold"},
    "pending":      {"stage": 3, "label": "Held for manual review",    "tone": "gold"},
    "issue":        {"stage": 2, "label": "Network issue detected",    "tone": "red"},
    "flagged":      {"stage": 3, "label": "Verification issue — hold", "tone": "red"},
    "completed":    {"stage": 4, "label": "Completed",                 "tone": "teal"},
}
LIVE_STATUS_CHOICES = [(key, meta["label"]) for key, meta in STAGE_META.items()]


class Balance(models.Model):
    """One row per customer: checking, savings, and a single fixed deposit."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="balance")
    checking = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    savings = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    fixed_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fixed_rate = models.DecimalField(max_digits=4, decimal_places=2, default=8.5, help_text="Annual %, e.g. 8.50")
    fixed_maturity = models.DateField(null=True, blank=True)
    fixed_term_months = models.PositiveIntegerField(default=18)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Balance({self.user})"


class Transaction(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Successful"
        PENDING = "pending", "Pending"
        DECLINED = "declined", "Failed"

    class Type(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=6, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, default="internal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user} · {self.description} · {self.amount}"

    def category_meta(self):
        return CATEGORY_META.get(self.category, CATEGORY_META["internal"])


class ExternalTransferDetail(models.Model):
    """Extra fields for the "Send to another bank" form — one per Transaction."""

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="external_detail")
    bank_name = models.CharField(max_length=100)
    recipient_account_number = models.CharField(max_length=32)
    recipient_name = models.CharField(max_length=150)
    narration = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.recipient_name} @ {self.bank_name}"


class LiveTransactionStatus(models.Model):
    """
    One row per customer holding their *current* live-monitor state. The
    admin dashboard writes to this; the customer dashboard polls it
    (GET /api/live-status/) roughly once a second. See asgi.py for the note
    on eventually replacing polling with a WebSocket push.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_status")
    status = models.CharField(max_length=14, choices=LIVE_STATUS_CHOICES, default="completed")
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, default="internal")
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def meta(self):
        return STAGE_META.get(self.status, STAGE_META["processing"])

    def as_dict(self):
        m = self.meta()
        return {
            "status": self.status,
            "stage": m["stage"],
            "label": m["label"],
            "tone": m["tone"],
            "category": self.category,
            "amount": float(self.amount) if self.amount is not None else None,
            "desc": self.description or None,
            "updated_at": self.updated_at.isoformat(),
        }

    def __str__(self):
        return f"Live({self.user} = {self.status})"


class SavingsGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def progress_pct(self):
        if not self.target_amount:
            return 0
        return min(100, round(float(self.current_amount) / float(self.target_amount) * 100))

    def __str__(self):
        return f"{self.name} ({self.user})"


class Notification(models.Model):
    class Audience(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        ADMIN = "admin", "Bank admin"

    # null user + audience=admin → shows in every admin's bell.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.CUSTOMER)
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=300)
    tone = models.CharField(max_length=10, default="teal")  # teal | gold | red — matches frontend dot colours
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
