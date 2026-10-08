from django.core.management.base import BaseCommand
from accounts.models import User


AUTH_USER_MODEL = "accounts.User"


class Command(BaseCommand):
    help = "Create the initial admin user if it does not exist"

    def handle(self, *args, **options):
        email = "admin.whitetrustbank.com@gmail.com"
        password = "White@2011@,"

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Admin {email} already exists.")
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Superuser {email} created successfully.")
        )