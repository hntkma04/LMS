# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "is_pinned", "created_at", "updated_at")
    list_filter = ("is_pinned", "created_at")
    search_fields = ("title", "user__email", "user__first_name", "user__last_name")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "conversation__title", "conversation__user__email")
