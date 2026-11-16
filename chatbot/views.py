# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from .service import generate_chat_response


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="chat")
    def chat(self, request):
        """Unified endpoint to send a message.
        If conversation_id is provided, attaches to it; otherwise creates a new conversation.
        """
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data["content"]
        conversation_id = serializer.validated_data.get("conversation_id")

        conversation = None
        if conversation_id:
            conversation = Conversation.objects.filter(
                id=conversation_id, user=request.user
            ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                title="Cuộc trò chuyện mới",
            )

        assistant_msg = generate_chat_response(conversation, content)
        # Fetch the user message that was just created right before assistant_msg
        user_msg = conversation.messages.filter(role=Message.ROLE_USER).last()

        return Response(
            {
                "conversation": ConversationListSerializer(conversation).data,
                "user_message": MessageSerializer(user_msg).data if user_msg else None,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="messages")
    def add_message(self, request, pk=None):
        """Send a message to an existing conversation."""
        conversation = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data["content"]
        assistant_msg = generate_chat_response(conversation, content)
        user_msg = conversation.messages.filter(role=Message.ROLE_USER).last()

        return Response(
            {
                "conversation": ConversationListSerializer(conversation).data,
                "user_message": MessageSerializer(user_msg).data if user_msg else None,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="clear")
    def clear_history(self, request, pk=None):
        """Clear all messages from this conversation."""
        conversation = self.get_object()
        conversation.messages.all().delete()
        conversation.title = "Cuộc trò chuyện mới"
        conversation.save(update_fields=["title", "updated_at"])
        return Response({"status": "cleared", "id": conversation.id})
