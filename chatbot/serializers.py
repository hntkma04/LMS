# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "created_at")
        read_only_fields = ("id", "role", "content", "created_at")


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source="messages.count", read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "is_pinned", "created_at", "updated_at", "message_count", "last_message")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if not last:
            return None
        return {
            "id": last.id,
            "role": last.role,
            "content": (last.content[:60] + "...") if len(last.content) > 60 else last.content,
            "created_at": last.created_at,
        }


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "is_pinned", "created_at", "updated_at", "messages")
        read_only_fields = ("id", "created_at", "updated_at", "messages")


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, allow_blank=False, max_length=10000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
