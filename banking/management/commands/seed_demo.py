from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from banking.models import Balance, LiveTransactionStatus, SavingsGoal, Transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds a demo bank admin and a demo customer with sample balances/transactions, matching the original static prototype."

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            email="admin@vaultra.bank",
            defaults={
                "username": "admin@vaultra.bank",
                "first_name": "Bank",
                "last_name": "Control",
                "role": User.Role.ADMIN,
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("admin1234")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin@vaultra.bank / admin1234"))
        else:
            self.stdout.write("admin@vaultra.bank already exists — skipping")

        customer, created = User.objects.get_or_create(
            email="demo@vaultra.bank",
            defaults={
                "username": "demo@vaultra.bank",
                "first_name": "Ada",
                "last_name": "Okafor",
                "role": User.Role.CUSTOMER,
            },
        )
        if created:
            customer.set_password("demo1234")
            customer.save()  # signal creates Balance/LiveTransactionStatus/welcome notification
            self.stdout.write(self.style.SUCCESS("Created demo@vaultra.bank / demo1234"))
        else:
            self.stdout.write("demo@vaultra.bank already exists — skipping")

        balance, _ = Balance.objects.get_or_create(user=customer)
        balance.checking = Decimal("4820.55")
        balance.savings = Decimal("12930.10")
        balance.fixed_amount = Decimal("25000.00")
        balance.fixed_rate = Decimal("8.50")
        balance.fixed_maturity = timezone.now().date() + timedelta(days=548)
        balance.fixed_term_months = 18
        balance.save()

        LiveTransactionStatus.objects.get_or_create(user=customer, defaults={"status": "completed"})

        if not customer.transactions.exists():
            today = timezone.now().date()
            demo_tx = [
                dict(description="Payroll — Halcyon Media", type="credit", amount="1450.00", status="completed", category="deposit", date=today - timedelta(days=4)),
                dict(description="Jumia Nigeria", type="debit", amount="62.40", status="completed", category="card", date=today - timedelta(days=5)),
                dict(description="Transfer to David M.", type="debit", amount="200.00", status="completed", category="internal", date=today - timedelta(days=6)),
                dict(description="Fixed deposit interest", type="credit", amount="84.30", status="completed", category="deposit", date=today - timedelta(days=8)),
                dict(description="Withdrawal request — ATM Wuse II", type="debit", amount="300.00", status="pending", category="withdrawal", date=today - timedelta(days=2)),
            ]
            for row in demo_tx:
                Transaction.objects.create(user=customer, **row)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(demo_tx)} demo transactions"))

        if not SavingsGoal.objects.filter(user=customer).exists():
            SavingsGoal.objects.create(user=customer, name="Emergency fund", target_amount="10000", current_amount="7200")
            SavingsGoal.objects.create(user=customer, name="New laptop", target_amount="1000", current_amount="450")
            SavingsGoal.objects.create(user=customer, name="December travel", target_amount="2000", current_amount="560")
            self.stdout.write(self.style.SUCCESS("Seeded 3 savings goals"))

        self.stdout.write(self.style.SUCCESS("Done. Log in at /accounts/login/"))
