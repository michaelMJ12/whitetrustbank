from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "account_number", "card_frozen", "is_active")
    list_filter = ("role", "card_frozen", "is_active")
    search_fields = ("email", "first_name", "last_name", "account_number")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Vaultra profile", {"fields": ("role", "account_number", "card_last4", "card_frozen", "phone")}),
    )
