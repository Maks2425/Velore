from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model. Authorization uses Django's built-in is_staff /
    is_superuser plus two business roles (Consultant, Admin) managed as
    Django Groups so the Super Admin can assign/revoke them from a plain
    group-membership screen instead of a bespoke permissions table.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", _("Клієнт")
        CONSULTANT = "consultant", _("Консультант")
        ADMIN = "admin", _("Адмін")
        SUPERADMIN = "superadmin", _("Супер Адмін")

    class Language(models.TextChoices):
        UKRAINIAN = "uk", "Українська"
        ENGLISH = "en", "English"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.UKRAINIAN)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, unique=True)
    telegram_link_code = models.CharField(max_length=64, blank=True)
    telegram_link_code_created_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    @property
    def role(self) -> str:
        if self.is_superuser:
            return self.Role.SUPERADMIN
        if self.groups.filter(name="Admin").exists():
            return self.Role.ADMIN
        if self.groups.filter(name="Consultant").exists():
            return self.Role.CONSULTANT
        return self.Role.CUSTOMER

    def get_role_display_name(self) -> str:
        return self.Role(self.role).label

    def __str__(self) -> str:
        return self.username
