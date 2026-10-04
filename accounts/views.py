import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .forms import RegistrationForm
from .models import User


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Вітаємо у Velore! Ваш обліковий запис створено.")
        return response


class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_superuser


class UserRoleListView(SuperAdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/role_management.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk).order_by("username").prefetch_related("groups")


class AssignRoleView(SuperAdminRequiredMixin, View):
    ROLE_TO_GROUP = {
        "admin": "Admin",
        "consultant": "Consultant",
        "customer": None,
    }

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        role = request.POST.get("role")

        if role not in self.ROLE_TO_GROUP:
            messages.error(request, "Невідома роль.")
            return redirect("accounts:role_management")

        if target_user.is_superuser:
            messages.error(request, "Неможливо змінити роль іншого Супер Адміна.")
            return redirect("accounts:role_management")

        target_user.groups.clear()
        group_name = self.ROLE_TO_GROUP[role]
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            target_user.groups.add(group)
            target_user.is_staff = True
        else:
            target_user.is_staff = False
        target_user.save(update_fields=["is_staff"])

        messages.success(request, f"Роль користувача {target_user.username} оновлено.")
        return redirect("accounts:role_management")


class TelegramLinkView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/telegram_link.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        bot = settings.TELEGRAM_BOT_USERNAME
        context["bot_username"] = bot
        context["linked"] = user.telegram_chat_id is not None
        code_fresh = (
            user.telegram_link_code
            and user.telegram_link_code_created_at
            and timezone.now() - user.telegram_link_code_created_at < timedelta(minutes=15)
        )
        if code_fresh and bot and not context["linked"]:
            context["code"] = user.telegram_link_code
            context["link_url"] = f"https://t.me/{bot}?start={user.telegram_link_code}"
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        user.telegram_link_code = secrets.token_urlsafe(16)
        user.telegram_link_code_created_at = timezone.now()
        user.save(update_fields=["telegram_link_code", "telegram_link_code_created_at"])
        return redirect("accounts:telegram_link")


class TelegramUnlinkView(LoginRequiredMixin, View):
    def post(self, request):
        User.objects.filter(pk=request.user.pk).update(telegram_chat_id=None, telegram_link_code="")
        messages.success(request, "Telegram відв'язано.")
        return redirect("accounts:telegram_link")
