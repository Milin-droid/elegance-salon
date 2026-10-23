import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the initial deployment administrator when credentials are configured."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username and not password:
            self.stdout.write("No deployment admin credentials configured; skipping.")
            return
        if not username or not password:
            raise ValueError(
                "Set both DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(
                self.style.SUCCESS(f"Created deployment admin '{username}'.")
            )
        elif not user.is_superuser:
            raise ValueError(
                f"Configured deployment admin '{username}' exists but is not a superuser."
            )
        else:
            self.stdout.write(
                f"Deployment admin '{username}' already exists; "
                "leaving its password unchanged."
            )
