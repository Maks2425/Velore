from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_logs_the_user_in(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "newbie",
            "email": "newbie@example.com",
            "phone": "",
            "password1": "Str0ngPass!2026",
            "password2": "Str0ngPass!2026",
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newbie").exists())
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username="existing", email="dup@example.com", password="pass12345")

        response = self.client.post(reverse("accounts:register"), {
            "username": "another",
            "email": "dup@example.com",
            "phone": "",
            "password1": "Str0ngPass!2026",
            "password2": "Str0ngPass!2026",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="another").exists())


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profileuser", email="old@example.com", password="pass12345")
        self.client.force_login(self.user)

    def test_user_can_update_email_and_phone(self):
        response = self.client.post(reverse("accounts:profile"), {"email": "new@example.com", "phone": "+380991112233"})

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.user.phone, "+380991112233")

    def test_anonymous_user_is_redirected(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)


class RoleAssignmentTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(username="boss", email="boss@example.com", password="pass12345")
        self.member = User.objects.create_user(username="member", email="member@example.com", password="pass12345")

    def test_superadmin_can_promote_to_consultant(self):
        self.client.force_login(self.superadmin)

        self.client.post(reverse("accounts:assign_role", args=[self.member.pk]), {"role": "consultant"})

        self.member.refresh_from_db()
        self.assertEqual(self.member.role, "consultant")
        self.assertTrue(self.member.is_staff)

    def test_regular_user_cannot_assign_roles(self):
        self.client.force_login(self.member)

        response = self.client.post(reverse("accounts:assign_role", args=[self.superadmin.pk]), {"role": "admin"})

        self.assertEqual(response.status_code, 403)


class PasswordResetTests(TestCase):
    def test_password_reset_sends_email_for_known_user(self):
        User.objects.create_user(username="forgetful", email="forgetful@example.com", password="pass12345")

        response = self.client.post(reverse("accounts:password_reset"), {"email": "forgetful@example.com"})

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["forgetful@example.com"])

    def test_password_reset_does_not_leak_whether_email_exists(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": "nobody@example.com"})

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
