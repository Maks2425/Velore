from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("roles/", views.UserRoleListView.as_view(), name="role_management"),
    path("roles/<int:pk>/assign/", views.AssignRoleView.as_view(), name="assign_role"),
]
