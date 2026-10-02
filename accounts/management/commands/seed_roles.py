from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the 'Admin' and 'Consultant' groups with their default permissions."

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        consultant_group, _ = Group.objects.get_or_create(name="Consultant")

        admin_perm_codenames = [
            "add_product", "change_product", "delete_product", "view_product",
            "add_brand", "change_brand", "delete_brand", "view_brand",
            "add_category", "change_category", "delete_category", "view_category",
            "view_order", "change_order",
            "view_user",
        ]
        consultant_perm_codenames = [
            "view_product", "view_brand", "view_category",
            "view_order", "change_order",
            "view_user",
        ]

        admin_group.permissions.set(Permission.objects.filter(codename__in=admin_perm_codenames))
        consultant_group.permissions.set(Permission.objects.filter(codename__in=consultant_perm_codenames))

        self.stdout.write(self.style.SUCCESS("Groups 'Admin' and 'Consultant' are ready."))
