from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role_display", "is_active", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Контакти", {"fields": ("phone",)}),
    )

    @admin.display(description="Роль")
    def role_display(self, obj: User) -> str:
        return obj.get_role_display_name()
