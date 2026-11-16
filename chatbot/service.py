# SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from pathlib import Path
from django.conf import settings
from tools.security_chatbot.client import (
    GeminiClient,
    ChatbotError,
    SafetyBlocked,
    GeminiAPIError,
    ModelUnavailable,
    RequestTimeout,
    ConnectionFailure,
)
from tools.security_chatbot.config import GeminiConfig, ConfigError
from tools.security_chatbot.prompts import SYSTEM_PROMPT
from .models import Conversation, Message

logger = logging.getLogger(__name__)


def get_gemini_config() -> GeminiConfig:
    env_file = Path(settings.BASE_DIR) / "tools" / "security_chatbot" / ".env"
    try:
        return GeminiConfig.from_env(env_file=env_file if env_file.exists() else None)
    except ConfigError as exc:
        logger.warning("Gemini configuration warning: %s", exc)
        raise


def generate_chat_response(conversation: Conversation, user_content: str) -> Message:
    """Send conversation messages to Gemini and record the assistant's reply."""
    config = get_gemini_config()
    client = GeminiClient(config)

    # 1. Save user message to database
    user_msg = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_USER,
        content=user_content,
    )

    # If first message or default title, generate a brief title from the prompt
    if conversation.title in ("Cuộc trò chuyện mới", "New Conversation", ""):
        snippet = user_content.strip()
        first_line = snippet.split("\n")[0]
        conversation.title = (first_line[:40] + "...") if len(first_line) > 40 else first_line
        conversation.save(update_fields=["title", "updated_at"])

    # 2. Collect history bounded by max_turns
    history_limit = max(config.max_turns * 2, 4)
    past_messages = list(
        conversation.messages.exclude(id=user_msg.id)
        .order_by("-created_at")[:history_limit]
    )
    past_messages.reverse()

    payload_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in past_messages:
        if msg.role in (Message.ROLE_USER, Message.ROLE_ASSISTANT):
            payload_messages.append({"role": msg.role, "content": msg.content})

    payload_messages.append({"role": "user", "content": user_content})

    # 3. Call Gemini
    try:
        reply_text = client.chat(payload_messages)
    except SafetyBlocked as exc:
        reply_text = f"Nội dung bị chặn bởi bộ lọc an toàn: {exc}"
    except (ConnectionFailure, RequestTimeout) as exc:
        reply_text = f"Không thể kết nối đến máy chủ AI (Timeout/Connection error): {exc}"
    except (GeminiAPIError, ModelUnavailable) as exc:
        reply_text = f"Đã xảy ra lỗi khi gọi AI ({exc})"
    except ChatbotError as exc:
        reply_text = f"Lỗi chatbot: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in chatbot service: %s", exc)
        reply_text = f"Hệ thống gặp sự cố khi xử lý câu trả lời: {exc}"

    # 4. Save assistant response
    assistant_msg = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=reply_text,
    )
    conversation.save(update_fields=["updated_at"])
    return assistant_msg
