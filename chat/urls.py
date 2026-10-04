from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("ai/", views.ai_chat, name="ai"),
    path("thread/", views.open_thread, name="open_thread"),
    path("thread/<int:thread_id>/messages/", views.thread_messages, name="messages"),
    path("thread/<int:thread_id>/send/", views.send_message, name="send"),
    path("manage/", views.InboxView.as_view(), name="inbox"),
    path("manage/<int:thread_id>/", views.thread_detail, name="thread"),
]
