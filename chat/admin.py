from django.contrib import admin

from .models import ChatMessage, ChatThread


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("sender", "author", "body", "created_at")


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("pk", "customer", "consultant", "is_open", "updated_at")
    list_filter = ("is_open",)
    list_select_related = ("customer", "consultant")
    inlines = [ChatMessageInline]
