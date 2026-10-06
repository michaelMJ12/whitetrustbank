from decimal import Decimal

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import ExternalTransferDetail, LiveTransactionStatus, Notification, Transaction


class ServiceError(Exception):
    """Raised for user-facing validation failures (insufficient funds, bad amount, ...)."""


def _notify(user, title, body, tone="teal", audience=Notification.Audience.CUSTOMER):
    Notification.objects.create(user=user, audience=audience, title=title, body=body, tone=tone)


def _notify_admins(title, body, tone="gold"):
    Notification.objects.create(user=None, audience=Notification.Audience.ADMIN, title=title, body=body, tone=tone)


@db_transaction.atomic
def withdraw(user, amount: Decimal):
    """Customer withdraws from checking. Requests over ₦200 are queued for admin review instead of clearing instantly."""
    balance = user.balance
    if amount <= 0:
        raise ServiceError("Enter a valid amount.")
    if amount > balance.checking:
        raise ServiceError("That exceeds your checking balance.")

    if amount > 200:
        tx = Transaction.objects.create(
            user=user, description="Withdrawal request", type=Transaction.Type.DEBIT,
            amount=amount, status=Transaction.Status.PENDING, category="withdrawal",
        )
        _notify(user, "Withdrawal submitted", f"Your ₦{amount:,.2f} withdrawal is queued for review.", tone="gold")
        _notify_admins("New withdrawal to review", f"{user.get_full_name() or user.email} requested ₦{amount:,.2f}.")
        return tx

    balance.checking -= amount
    balance.save(update_fields=["checking"])
    tx = Transaction.objects.create(
        user=user, description="ATM withdrawal", type=Transaction.Type.DEBIT,
        amount=amount, status=Transaction.Status.COMPLETED, category="withdrawal",
    )
    return tx


@db_transaction.atomic
def transfer_savings_to_checking(user, amount: Decimal):
    balance = user.balance
    if amount <= 0:
        raise ServiceError("Enter a valid amount.")
    if amount > balance.savings:
        raise ServiceError("That exceeds your savings balance.")

    balance.savings -= amount
    balance.checking += amount
    balance.save(update_fields=["savings", "checking"])
    Transaction.objects.create(
        user=user, description="Transfer from savings", type=Transaction.Type.CREDIT,
        amount=amount, status=Transaction.Status.COMPLETED, category="internal",
    )
    return Transaction.objects.create(
        user=user, description="Transfer to checking", type=Transaction.Type.DEBIT,
        amount=amount, status=Transaction.Status.COMPLETED, category="internal",
    )


@db_transaction.atomic
def send_external_transfer(user, *, bank_name, recipient_account_number, recipient_name, amount: Decimal, narration=""):
    """Customer-initiated interbank transfer. Debited immediately, queued pending — the live monitor tracks it from there."""
    balance = user.balance
    if amount <= 0:
        raise ServiceError("Enter a valid amount.")
    if amount > balance.checking:
        raise ServiceError("That exceeds your checking balance.")

    balance.checking -= amount
    balance.save(update_fields=["checking"])

    tx = Transaction.objects.create(
        user=user,
        description=f"Transfer to {recipient_name} — {bank_name}",
        type=Transaction.Type.DEBIT,
        amount=amount,
        status=Transaction.Status.PENDING,
        category="external",
    )
    ExternalTransferDetail.objects.create(
        transaction=tx, bank_name=bank_name, recipient_account_number=recipient_account_number,
        recipient_name=recipient_name, narration=narration,
    )
    set_live_status(
        user, "processing", category="external", amount=amount,
        description=f"{narration or 'Transfer'} to {recipient_name} — {bank_name}",
    )
    _notify(user, "External transfer submitted", f"₦{amount:,.2f} to {recipient_name} at {bank_name} is being processed.", tone="gold")
    _notify_admins("New interbank transfer", f"{user.get_full_name() or user.email} sent ₦{amount:,.2f} to {bank_name}.")
    return tx


@db_transaction.atomic
def admin_adjust_balance(user, account: str, direction: str, amount: Decimal):
    """Admin control: credit or debit a customer's checking / savings / fixed deposit directly."""
    if amount <= 0:
        raise ServiceError("Enter a valid amount.")
    delta = amount if direction == "credit" else -amount
    balance = user.balance

    if account == "fixed":
        balance.fixed_amount = max(Decimal("0"), balance.fixed_amount + delta)
        balance.save(update_fields=["fixed_amount"])
    elif account in ("checking", "savings"):
        current = getattr(balance, account)
        setattr(balance, account, max(Decimal("0"), current + delta))
        balance.save(update_fields=[account])
    else:
        raise ServiceError("Unknown account type.")

    Transaction.objects.create(
        user=user,
        description="Credit Entry" if delta >= 0 else "Debit Entry",
        type=Transaction.Type.CREDIT if delta >= 0 else Transaction.Type.DEBIT,
        amount=abs(delta), status=Transaction.Status.COMPLETED, category="admin",
    )
    _notify(
        user, "Funds credited" if delta >= 0 else "Funds debited",
        f"Bank control {'credited' if delta >= 0 else 'debited'} ₦{abs(delta):,.2f} on your {account} account.",
        tone="teal" if delta >= 0 else "gold",
    )


@db_transaction.atomic
def set_transaction_status(tx: Transaction, status: str):
    """Admin approves/declines a pending transaction. Approving a pending debit finally deducts the balance."""
    was_pending = tx.status == Transaction.Status.PENDING
    tx.status = status
    tx.save(update_fields=["status"])

    if was_pending and status == Transaction.Status.COMPLETED and tx.type == Transaction.Type.DEBIT:
        balance = tx.user.balance
        balance.checking = max(Decimal("0"), balance.checking - tx.amount)
        balance.save(update_fields=["checking"])

    _notify(
        tx.user, "Transaction approved" if status == Transaction.Status.COMPLETED else "Transaction declined",
        f'"{tx.description}" for ₦{tx.amount:,.2f} was '
        f'{"approved and cleared" if status == Transaction.Status.COMPLETED else "declined"} by bank control.',
        tone="teal" if status == Transaction.Status.COMPLETED else "red",
    )


def toggle_card_freeze(user):
    user.card_frozen = not user.card_frozen
    user.save(update_fields=["card_frozen"])
    _notify(
        user, "Card frozen" if user.card_frozen else "Card unfrozen",
        "Your debit card was frozen. New purchases and withdrawals will decline."
        if user.card_frozen else "Your debit card is active again.",
        tone="red" if user.card_frozen else "teal",
    )
    return user.card_frozen


def set_live_status(user, status: str, *, category=None, amount=None, description=None):
    """The single write-path for the live heartbeat monitor — used by both the admin API and internal service calls above."""
    live, _ = LiveTransactionStatus.objects.get_or_create(user=user)
    live.status = status
    if category:
        live.category = category
    if amount is not None:
        live.amount = amount
    if description is not None:
        live.description = description
    live.updated_at = timezone.now()
    live.save()

    if status in ("completed", "issue", "flagged"):
        _notify(
            user,
            {"completed": "Transaction completed", "issue": "Network issue detected", "flagged": "Verification issue"}[status],
            f"{live.description}{f' · ₦{live.amount:,.2f}' if live.amount else ''}" if live.description else "Your live transaction status changed.",
            tone="teal" if status == "completed" else "red",
        )
    return live
