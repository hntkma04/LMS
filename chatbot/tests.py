# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from chatbot.models import Conversation, Message

User = get_user_model()


class ChatbotModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
        )

    def test_create_conversation_and_messages(self):
        conv = Conversation.objects.create(
            user=self.user,
            title="Kiểm tra an toàn ứng dụng",
        )
        msg1 = Message.objects.create(
            conversation=conv,
            role=Message.ROLE_USER,
            content="Xin chào chatbot",
        )
        msg2 = Message.objects.create(
            conversation=conv,
            role=Message.ROLE_ASSISTANT,
            content="Chào bạn! Tôi có thể giúp gì cho bạn?",
        )

        self.assertEqual(conv.messages.count(), 2)
        self.assertEqual(conv.messages.first().content, "Xin chào chatbot")
        self.assertEqual(conv.messages.last().content, "Chào bạn! Tôi có thể giúp gì cho bạn?")


class ChatbotApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="apiuser@example.com",
            password="testpassword123",
            first_name="Api",
            last_name="User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_conversations(self):
        Conversation.objects.create(user=self.user, title="Chat 1")
        Conversation.objects.create(user=self.user, title="Chat 2")

        res = self.client.get("/api/chatbot/conversations/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Handle paginated or unpaginated response
        results = res.data.get("results") if isinstance(res.data, dict) and "results" in res.data else res.data
        self.assertEqual(len(results), 2)

    @patch("chatbot.service.GeminiClient.chat")
    def test_send_chat_message(self, mock_chat):
        mock_chat.return_value = "Đây là phản hồi AI bảo mật."

        res = self.client.post(
            "/api/chatbot/conversations/chat/",
            {"content": "Làm thế nào để bảo mật API?"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        self.assertIn("conversation", data)
        self.assertIn("user_message", data)
        self.assertIn("assistant_message", data)
        self.assertEqual(data["assistant_message"]["content"], "Đây là phản hồi AI bảo mật.")

        conv_id = data["conversation"]["id"]
        conv = Conversation.objects.get(id=conv_id)
        self.assertEqual(conv.messages.count(), 2)
