from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Create (or update) the Super Admin account from SUPERADMIN_EMAIL / "
        "SUPERADMIN_USERNAME / SUPERADMIN_PASSWORD in the environment (.env). "
        "The password is never printed or stored in plain text — Django hashes "
        "it via set_password()."
    )

    def handle(self, *args, **options):
        email = settings.SUPERADMIN_EMAIL
        username = settings.SUPERADMIN_USERNAME
        password = settings.SUPERADMIN_PASSWORD

        if not email or not password:
            raise CommandError(
                "SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must be set in .env "
                "(copy .env.example and fill them in) before running this command."
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "is_staff": True, "is_superuser": True},
        )
        user.username = username
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Super Admin account {action}: {username} <{email}>"))
