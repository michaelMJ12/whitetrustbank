from django.urls import path

from . import views

app_name = "banking"

urlpatterns = [
    # Pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("bank-control/", views.admin_dashboard, name="admin_dashboard"),

    # Shared
    path("api/meta/", views.api_meta, name="api_meta"),

    # Customer API
    path("api/balance/", views.api_balance, name="api_balance"),
    path("api/transactions/", views.api_transactions, name="api_transactions"),
    path("api/live-status/", views.api_live_status, name="api_live_status"),
    path("api/notifications/", views.api_notifications, name="api_notifications"),
    path("api/notifications/mark-all-read/", views.api_notifications_mark_read, name="api_notifications_mark_read"),
    path("api/withdraw/", views.api_withdraw, name="api_withdraw"),
    path("api/transfer/", views.api_transfer, name="api_transfer"),
    path("api/external-transfer/", views.api_external_transfer, name="api_external_transfer"),
    path("api/card/toggle-freeze/", views.api_toggle_freeze, name="api_toggle_freeze"),

    # Admin API
    path("api/admin/stats/", views.api_admin_stats, name="api_admin_stats"),
    path("api/admin/transactions/", views.api_admin_transactions, name="api_admin_transactions"),
    path("api/admin/pending/", views.api_admin_pending, name="api_admin_pending"),
    path("api/admin/accounts/", views.api_admin_accounts, name="api_admin_accounts"),
    path("api/admin/accounts/<int:user_id>/adjust-balance/", views.api_admin_adjust_balance, name="api_admin_adjust_balance"),
    path("api/admin/accounts/<int:user_id>/toggle-freeze/", views.api_admin_toggle_freeze, name="api_admin_toggle_freeze"),
    path("api/admin/transactions/<uuid:tx_id>/set-status/", views.api_admin_transaction_set_status, name="api_admin_transaction_set_status"),
    path("api/admin/live-status/", views.api_admin_live_status_list, name="api_admin_live_status_list"),
    path("api/admin/live-status/<int:user_id>/set/", views.api_admin_live_status_set, name="api_admin_live_status_set"),
    path("api/admin/notifications/", views.api_admin_notifications, name="api_admin_notifications"),
    path("api/admin/notifications/mark-all-read/", views.api_admin_notifications_mark_read, name="api_admin_notifications_mark_read"),
]
