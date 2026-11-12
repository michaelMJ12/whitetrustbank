from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from .forms import AdminTransactionDateTimeForm
from . import services
from . import services
from .decorators import admin_required, customer_required, json_post_required
from .forms import (
    AdminAdjustBalanceForm,
    AdminLiveStatusForm,
    AdminTransactionStatusForm,
    AmountForm,
    ExternalTransferForm,
)
from .models import (
    CATEGORY_META,
    STAGE_META,
    LiveTransactionStatus,
    Notification,
    SavingsGoal,
    Transaction,
)
from .services import ServiceError
from .utils import smart_table_response

User = get_user_model()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def landing_page(request):
    return render(request, "landing/index.html")


@customer_required
def dashboard(request):
    user = request.user

    context = {
        "balance": user.balance,
        "savings_goals": SavingsGoal.objects.filter(user=user),
        "recent_transactions": user.transactions.all()[:5],
        "category_meta": CATEGORY_META,
    }

    return render(request, "dashboard/customer_dashboard.html", context)


@admin_required
def admin_dashboard(request):
    context = {
        "category_meta": CATEGORY_META,
        "stage_meta": STAGE_META,
    }

    return render(request, "dashboard/admin_dashboard.html", context)


# ---------------------------------------------------------------------------
# Shared meta
# ---------------------------------------------------------------------------

@require_GET
def api_meta(request):
    return JsonResponse({
        "categories": CATEGORY_META,
        "stages": STAGE_META,
    })


# ---------------------------------------------------------------------------
# Customer API
# ---------------------------------------------------------------------------

def _serialize_transaction(tx):
    return {
        "id": str(tx.id),
        "date": tx.date.isoformat(),
        "desc": tx.description,
        "type": tx.type,
        "amount": float(tx.amount),
        "status": tx.status,
        "category": tx.category,
    }


def _serialize_transaction_admin(tx):
    data = _serialize_transaction(tx)

    data.update({
        "userId": tx.user_id,
        "customer": tx.user.get_full_name() or tx.user.email,
        "accountNumber": tx.user.account_number,
    })

    return data


@customer_required
@require_GET
def api_transactions(request):
    qs = request.user.transactions.all()

    data = smart_table_response(
        request,
        qs,
        search_fields=["description"],
        filter_fields=["status", "category"],
        serialize=_serialize_transaction,
        default_sort="-date",
    )

    return JsonResponse(data)


@customer_required
@require_GET
def api_live_status(request):
    live, _ = LiveTransactionStatus.objects.get_or_create(
        user=request.user
    )

    return JsonResponse(live.as_dict())


@customer_required
@require_GET
def api_notifications(request):
    """
    Return the customer's latest 20 notifications.

    IMPORTANT:
    Do not slice the QuerySet before calling .filter().
    Django does not allow filtering a sliced QuerySet.
    """

    queryset = Notification.objects.filter(
        user=request.user,
        audience=Notification.Audience.CUSTOMER,
    ).order_by("-created_at")

    # Count unread notifications BEFORE slicing the queryset.
    unread = queryset.filter(read=False).count()

    # Slice only after all filtering/counting is complete.
    notifs = queryset[:20]

    return JsonResponse({
        "results": [_serialize_notification(n) for n in notifs],
        "unread": unread,
    })


def _serialize_notification(n):
    return {
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "tone": n.tone,
        "read": n.read,
        "date": n.created_at.date().isoformat(),
    }


@customer_required
@json_post_required
def api_notifications_mark_read(request):
    Notification.objects.filter(
        user=request.user,
        audience=Notification.Audience.CUSTOMER,
        read=False,
    ).update(read=True)

    return JsonResponse({"ok": True})


@customer_required
@json_post_required
def api_withdraw(request):
    form = AmountForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Enter a valid amount.",
            },
            status=400,
        )

    try:
        services.withdraw(
            request.user,
            form.cleaned_data["amount"],
        )
    except ServiceError as e:
        return JsonResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status=400,
        )

    return JsonResponse({
        "ok": True,
        "balance": _serialize_balance(request.user),
    })


@customer_required
@json_post_required
def api_transfer(request):
    form = AmountForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Enter a valid amount.",
            },
            status=400,
        )

    try:
        services.transfer_savings_to_checking(
            request.user,
            form.cleaned_data["amount"],
        )
    except ServiceError as e:
        return JsonResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status=400,
        )

    return JsonResponse({
        "ok": True,
        "balance": _serialize_balance(request.user),
    })


@customer_required
@json_post_required
def api_external_transfer(request):
    form = ExternalTransferForm(request.POST)

    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]

        return JsonResponse(
            {
                "ok": False,
                "error": first_error,
            },
            status=400,
        )

    try:
        services.send_external_transfer(
            request.user,
            bank_name=form.cleaned_data["bank_name"],
            recipient_account_number=form.cleaned_data[
                "recipient_account_number"
            ],
            recipient_name=form.cleaned_data["recipient_name"],
            amount=form.cleaned_data["amount"],
            narration=form.cleaned_data["narration"],
        )
    except ServiceError as e:
        return JsonResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status=400,
        )

    return JsonResponse({
        "ok": True,
        "balance": _serialize_balance(request.user),
    })


@customer_required
@json_post_required
def api_toggle_freeze(request):
    frozen = services.toggle_card_freeze(request.user)

    return JsonResponse({
        "ok": True,
        "cardFrozen": frozen,
    })


def _serialize_balance(user):
    b = user.balance

    return {
        "checking": float(b.checking),
        "savings": float(b.savings),
        "fixed": {
            "amount": float(b.fixed_amount),
            "rate": float(b.fixed_rate),
            "maturity": (
                b.fixed_maturity.isoformat()
                if b.fixed_maturity
                else None
            ),
        },
        "cardFrozen": user.card_frozen,
        "cardLast4": user.card_last4,
    }


@customer_required
@require_GET
def api_balance(request):
    return JsonResponse(
        _serialize_balance(request.user)
    )


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------

@admin_required
@require_GET
def api_admin_stats(request):
    from django.db.models import Sum

    users = User.objects.filter(role="customer")

    totals = users.aggregate(
        total_checking=Sum("balance__checking"),
        total_savings=Sum("balance__savings"),
        total_fixed=Sum("balance__fixed_amount"),
    )

    pending_count = Transaction.objects.filter(
        status=Transaction.Status.PENDING
    ).count()

    return JsonResponse({
        "accounts": users.count(),
        "totalLiquid": float(
            (totals["total_checking"] or 0)
            + (totals["total_savings"] or 0)
        ),
        "totalFixed": float(
            totals["total_fixed"] or 0
        ),
        "pending": pending_count,
    })


@admin_required
@require_GET
def api_admin_transactions(request):
    qs = Transaction.objects.select_related("user")

    data = smart_table_response(
        request,
        qs,
        search_fields=[
            "description",
            "user__first_name",
            "user__last_name",
            "user__email",
        ],
        filter_fields=["status", "category"],
        serialize=_serialize_transaction_admin,
        default_sort="-date",
    )

    return JsonResponse(data)


@admin_required
@require_GET
def api_admin_pending(request):
    qs = (
        Transaction.objects
        .select_related("user")
        .filter(status=Transaction.Status.PENDING)
    )

    data = smart_table_response(
        request,
        qs,
        search_fields=[
            "description",
            "user__first_name",
            "user__last_name",
            "user__email",
        ],
        filter_fields=["category"],
        serialize=_serialize_transaction_admin,
        default_sort="-date",
    )

    return JsonResponse(data)


def _serialize_account(u):
    b = u.balance

    return {
        "id": u.id,
        "name": u.get_full_name() or u.email,
        "accountNumber": u.account_number,
        "checking": float(b.checking),
        "savings": float(b.savings),
        "fixed": float(b.fixed_amount),
        "cardStatus": "Frozen" if u.card_frozen else "Active",
    }


# Maps the smart table's flat column keys to the real ORM
# lookup needed to sort on them.
ACCOUNT_SORT_FIELDS = {
    "name": "first_name",
    "checking": "balance__checking",
    "savings": "balance__savings",
    "fixed": "balance__fixed_amount",
    "cardStatus": "card_frozen",
}


@admin_required
@require_GET
def api_admin_accounts(request):
    qs = (
        User.objects.filter(role="customer", is_active=True).select_related("balance")
    )

    search = request.GET.get("search", "").strip()

    if search:
        from django.db.models import Q

        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(account_number__icontains=search)
        )

    card_status = request.GET.get("cardStatus")

    if card_status == "Frozen":
        qs = qs.filter(card_frozen=True)

    elif card_status == "Active":
        qs = qs.filter(card_frozen=False)

    sort_key = request.GET.get("sort")
    sort_dir = request.GET.get("dir", "asc")

    order_field = ACCOUNT_SORT_FIELDS.get(
        sort_key,
        "first_name",
    )

    if sort_dir == "asc":
        qs = qs.order_by(order_field)
    else:
        qs = qs.order_by(f"-{order_field}")

    from django.core.paginator import Paginator

    page_size = min(
        int(request.GET.get("page_size", 8) or 8),
        100,
    )

    paginator = Paginator(
        qs,
        page_size,
    )

    page = paginator.get_page(
        int(request.GET.get("page", 1) or 1)
    )

    return JsonResponse({
        "results": [
            _serialize_account(u)
            for u in page.object_list
        ],
        "total": paginator.count,
        "page": page.number,
        "pages": paginator.num_pages,
    })


@admin_required
@json_post_required
def api_admin_adjust_balance(request, user_id):
    user = get_object_or_404(
        User,
        pk=user_id,
        role="customer",
    )

    form = AdminAdjustBalanceForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Enter a valid amount.",
            },
            status=400,
        )

    try:
        services.admin_adjust_balance(
            user,
            form.cleaned_data["account"],
            form.cleaned_data["direction"],
            form.cleaned_data["amount"],
        )
    except ServiceError as e:
        return JsonResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status=400,
        )

    return JsonResponse({"ok": True})


@admin_required
@json_post_required
def api_admin_toggle_freeze(request, user_id):
    user = get_object_or_404(
        User,
        pk=user_id,
        role="customer",
    )

    frozen = services.toggle_card_freeze(user)

    return JsonResponse({
        "ok": True,
        "cardFrozen": frozen,
    })


@admin_required
@json_post_required
def api_admin_transaction_set_status(request, tx_id):
    tx = get_object_or_404(
        Transaction,
        pk=tx_id,
    )

    form = AdminTransactionStatusForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Invalid status.",
            },
            status=400,
        )

    services.set_transaction_status(
        tx,
        form.cleaned_data["status"],
    )

    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Live transaction control (the "heartbeat")
# ---------------------------------------------------------------------------

@admin_required
@require_GET
def api_admin_live_status_list(request):
    """
    Every customer's current live status, for the admin monitor grid.
    """

    customers = (
        User.objects
        .filter(role="customer")
        .select_related("live_status", "balance")
    )

    out = {}

    for u in customers:
        live, _ = LiveTransactionStatus.objects.get_or_create(
            user=u
        )

        out[u.id] = {
            **live.as_dict(),
            "name": u.get_full_name() or u.email,
            "accountNumber": u.account_number,
        }

    return JsonResponse({
        "results": out,
    })


@admin_required
@json_post_required
def api_admin_live_status_set(request, user_id):
    """
    Admin sets one customer's live status directly.

    To animate a pipeline
    (submitted → network → verification → completed/issue),
    the admin dashboard JS calls this endpoint several times
    a couple of seconds apart.

    The endpoint remains a plain, fast, single database write.
    """

    user = get_object_or_404(
        User,
        pk=user_id,
        role="customer",
    )

    form = AdminLiveStatusForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Invalid status update.",
            },
            status=400,
        )

    cleaned = form.cleaned_data

    live = services.set_live_status(
        user,
        cleaned["status"],
        category=cleaned.get("category") or None,
        amount=cleaned.get("amount"),
        description=cleaned.get("description") or None,
    )

    return JsonResponse({
        "ok": True,
        "live": live.as_dict(),
    })


@admin_required
@require_GET
def api_admin_notifications(request):
    """
    Return the latest 20 admin notifications.

    IMPORTANT:
    Calculate unread BEFORE slicing the QuerySet.
    Filtering a QuerySet after [:20] causes:

        TypeError:
        Cannot filter a query once a slice has been taken.
    """

    queryset = Notification.objects.filter(
        audience=Notification.Audience.ADMIN,
    ).order_by("-created_at")

    # Count unread notifications before slicing.
    unread = queryset.filter(
        read=False
    ).count()

    # Only slice after filtering/counting.
    notifs = queryset[:20]

    return JsonResponse({
        "results": [
            _serialize_notification(n)
            for n in notifs
        ],
        "unread": unread,
    })


@admin_required
@json_post_required
def api_admin_notifications_mark_read(request):
    Notification.objects.filter(
        audience=Notification.Audience.ADMIN,
        read=False,
    ).update(read=True)

    return JsonResponse({"ok": True})


@admin_required
@json_post_required
def api_admin_delete_account(request, user_id):
    user = get_object_or_404(User, pk=user_id, role="customer")

    if request.POST.get("confirm") != user.account_number:
        return JsonResponse(
            {"ok": False, "error": "Type the account number to confirm."},
            status=400,
        )

    permanent = request.POST.get("permanent") == "true"

    try:
        services.admin_delete_account(user, permanent=permanent)
    except ServiceError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True})


@admin_required
@json_post_required
def api_admin_transaction_edit_datetime(request, tx_id):
    """
    Admin-only transaction date and time correction endpoint.
    """

    tx = get_object_or_404(Transaction, id=tx_id)

    form = AdminTransactionDateTimeForm(request.POST)

    if not form.is_valid():
        return JsonResponse({
            "success": False,
            "errors": form.errors,
        }, status=400)

    try:
        tx = services.admin_edit_transaction_datetime(
            transaction_id=tx.id,
            admin_user=request.user,
            new_date=form.cleaned_data["date"],
            new_time=form.cleaned_data["time"],
            reason=form.cleaned_data["reason"],
        )

        return JsonResponse({
            "success": True,
            "message": "Transaction date and time updated successfully.",
            "transaction": {
                "id": str(tx.id),
                "date": tx.date.isoformat(),
                "time": timezone.localtime(
                    tx.created_at
                ).strftime("%H:%M:%S"),
                "datetime": timezone.localtime(
                    tx.created_at
                ).isoformat(),
            },
        })

    except Transaction.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Transaction not found.",
        }, status=404)

    except services.ServiceError as exc:
        return JsonResponse({
            "success": False,
            "message": str(exc),
        }, status=400)



    

































   


























































































































































































































































































   

from django.core.cache import cache

SYSTEM_SHUTDOWN_KEY = "system_shutdown"


@admin_required
@json_post_required
def api_admin_system_shutdown(request):
    """
    Put the platform into shutdown (maintenance) mode.

    While shutdown is active, all non-admin traffic is blocked.
    Admins can still log in and manage the platform.

    POST body (optional):
        message - custom message shown to blocked users
    """

    cache.set(
        SYSTEM_SHUTDOWN_KEY,
        {
            "active": True,
            "message": request.POST.get(
                "message", "System is temporarily down for maintenance."
            ),
            "activated_by": request.user.get_full_name() or request.user.email,
            "activated_at": timezone.now().isoformat(),
        },
        timeout=None,  # persists until explicitly cleared
    )

    return JsonResponse({
        "ok": True,
        "shutdown": True,
        "activatedAt": timezone.now().isoformat(),
    })


@admin_required
@json_post_required
def api_admin_system_startup(request):
    """Bring the platform back online after a shutdown."""

    cache.set(SYSTEM_SHUTDOWN_KEY, {"active": False}, timeout=None)

    return JsonResponse({
        "ok": True,
        "shutdown": False,
    })


@admin_required
@require_GET
def api_admin_system_status(request):
    """Check whether the system is currently shut down."""

    state = cache.get(SYSTEM_SHUTDOWN_KEY) or {"active": False}

    return JsonResponse({
        "ok": True,
        "shutdown": state.get("active", False),
        "details": state,
    })