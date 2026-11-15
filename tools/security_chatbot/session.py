"""In-memory, bounded conversation state."""

from __future__ import annotations

from .client import GeminiClient
from .config import GeminiConfig
from .prompts import SYSTEM_PROMPT


def normalize_terminal_text(text: str) -> str:
    """Replace unpaired UTF-16 surrogates produced by terminal decoding."""
    return "".join("\N{REPLACEMENT CHARACTER}" if 0xD800 <= ord(char) <= 0xDFFF else char for char in text)


class ChatSession:
    def __init__(self, config: GeminiConfig, client: GeminiClient, system_prompt: str = SYSTEM_PROMPT) -> None:
        self.config = config
        self.client = client
        self.system_prompt = system_prompt
        self.clear()

    def clear(self) -> None:
        self.messages: list[dict[str, str]] = [{"role": "system", "content": self.system_prompt}]

    def ask(self, text: str) -> str:
        text = normalize_terminal_text(text)
        self.messages.append({"role": "user", "content": text})
        try:
            answer = self.client.chat(self.messages)
        except Exception:
            self.messages.pop()
            raise
        self.messages.append({"role": "assistant", "content": answer})
        history = self.messages[1:]
        self.messages = [self.messages[0], *history[-self.config.max_turns * 2:]]
        return answer
