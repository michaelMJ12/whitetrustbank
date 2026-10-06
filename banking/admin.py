from django.contrib import admin

from .models import Balance, ExternalTransferDetail, LiveTransactionStatus, Notification, SavingsGoal, Transaction


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "checking", "savings", "fixed_amount", "fixed_rate", "fixed_maturity")
    search_fields = ("user__email", "user__first_name", "user__last_name")


class ExternalTransferInline(admin.StackedInline):
    model = ExternalTransferDetail
    extra = 0


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "description", "type", "amount", "status", "category")
    list_filter = ("status", "category", "type")
    search_fields = ("description", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "date"
    inlines = [ExternalTransferInline]


@admin.register(LiveTransactionStatus)
class LiveTransactionStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "category", "amount", "updated_at")
    list_filter = ("status", "category")


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "target_amount", "current_amount")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "user", "tone", "read", "created_at")
    list_filter = ("audience", "tone", "read")
