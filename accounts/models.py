import random

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


def _generate_account_number() -> str:
    """0091 XXXX XXXX — matches the format already used across the frontend."""
    return "0091 %04d %04d" % (
        random.randint(0, 9999),
        random.randint(0, 9999),
    )


def _generate_card_last4() -> str:
    return "%04d" % random.randint(0, 9999)


class UserManager(DjangoUserManager):
    """
    Custom manager for Vaultra users.

    Normal users created through the application remain customers.

    Django superusers created with:

        python manage.py createsuperuser

    are automatically assigned the Vaultra ADMIN role.
    """

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # A Django superuser is also a Vaultra bank administrator.
        extra_fields["role"] = self.model.Role.ADMIN

        # Admin users should not receive customer banking details.
        extra_fields.setdefault("account_number", None)
        extra_fields.setdefault("card_last4", "")

        return self._create_user(
            username,
            email,
            password,
            **extra_fields,
        )


class User(AbstractUser):
    """
    One table for everybody.

    `role` determines which Vaultra dashboard a user lands on
    and which application-level permissions they have.

    Django's `is_staff` and `is_superuser` remain independent and
    are reserved for Django administration.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        ADMIN = "admin", "Bank admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    # Customer-facing account details.
    # These remain blank for admin users.
    account_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

    card_last4 = models.CharField(
        max_length=4,
        blank=True,
    )

    card_frozen = models.BooleanField(
        default=False,
    )

    phone = models.CharField(
        max_length=32,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    objects = UserManager()

    def save(self, *args, **kwargs):
        """
        Generate customer banking details automatically.

        Admin users do not receive an account number or card details.
        """

        if self.role == self.Role.CUSTOMER:

            if not self.account_number:
                self.account_number = _generate_account_number()

            if not self.card_last4:
                self.card_last4 = _generate_card_last4()

        else:
            # Bank admins do not need customer banking details.
            self.account_number = None
            self.card_last4 = ""

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_bank_admin(self) -> bool:
        return self.role == self.Role.ADMIN
