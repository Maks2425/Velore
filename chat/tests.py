import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ChatThread

User = get_user_model()


@override_settings(OPENAI_API_KEY="")
class AIChatTests(TestCase):
    def test_ai_chat_without_api_key_returns_503(self):
        response = self.client.post(
            reverse("chat:ai"),
            data=json.dumps({"messages": [{"role": "user", "content": "Привіт"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)

    def test_ai_chat_rejects_malformed_payload(self):
        response = self.client.post(reverse("chat:ai"), data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)


class ConsultantChatTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="client1", email="client1@example.com", password="pass12345")
        self.consultant = User.objects.create_user(
            username="agent1", email="agent1@example.com", password="pass12345", is_staff=True
        )
        self.stranger = User.objects.create_user(username="stranger1", email="stranger1@example.com", password="pass12345")

    def test_open_thread_requires_login(self):
        response = self.client.post(reverse("chat:open_thread"))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_open_and_send(self):
        self.client.force_login(self.customer)

        response = self.client.post(reverse("chat:open_thread"))
        thread_id = response.json()["thread_id"]

        self.client.post(
            reverse("chat:send", args=[thread_id]),
            data=json.dumps({"body": "Потрібна допомога"}),
            content_type="application/json",
        )

        thread = ChatThread.objects.get(pk=thread_id)
        self.assertEqual(thread.messages.count(), 1)
        self.assertEqual(thread.messages.get().sender, "customer")

    def test_stranger_cannot_read_thread(self):
        thread = ChatThread.objects.create(customer=self.customer)
        self.client.force_login(self.stranger)

        response = self.client.get(reverse("chat:messages", args=[thread.pk]))

        self.assertEqual(response.status_code, 403)

    def test_consultant_reply_assigns_consultant_and_is_visible_to_customer(self):
        thread = ChatThread.objects.create(customer=self.customer)
        self.client.force_login(self.consultant)

        self.client.post(
            reverse("chat:send", args=[thread.pk]),
            data=json.dumps({"body": "Вітаю, чим допомогти?"}),
            content_type="application/json",
        )

        thread.refresh_from_db()
        self.assertEqual(thread.consultant, self.consultant)
        message = thread.messages.get()
        self.assertEqual(message.sender, "consultant")

    def test_inbox_requires_staff(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 403)
