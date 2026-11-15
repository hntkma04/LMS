"""Minimal Gemini generateContent REST client with safe error handling."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Callable, Protocol
from urllib import parse

import requests

from .config import GeminiConfig


class ChatbotError(RuntimeError):
    pass


class ConnectionFailure(ChatbotError):
    pass


class RequestTimeout(ChatbotError):
    pass


class GeminiAPIError(ChatbotError):
    pass


class ModelUnavailable(ChatbotError):
    pass


class InvalidResponse(ChatbotError):
    pass


class SafetyBlocked(ChatbotError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes


class Transport(Protocol):
    def send(self, method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> HttpResponse:
        ...


class RequestsTransport:
    def send(self, method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> HttpResponse:
        try:
            response = requests.request(method, url, headers=headers, data=body, timeout=timeout)
            return HttpResponse(response.status_code, response.content)
        except requests.Timeout as exc:
            raise RequestTimeout("Gemini API timed out") from exc
        except requests.RequestException as exc:
            raise ConnectionFailure("Cannot connect to Gemini API") from exc


class GeminiClient:
    def __init__(
        self,
        config: GeminiConfig,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.transport = transport or RequestsTransport()
        self.sleep = sleep

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-goog-api-key": self.config.api_key,
        }

    def _safe_detail(self, body: bytes) -> str:
        try:
            payload = json.loads(body.decode("utf-8"))
            detail = payload.get("error", payload)
            if isinstance(detail, dict):
                detail = detail.get("message", detail.get("status", "Gemini API error"))
            text = str(detail)
        except (UnicodeDecodeError, json.JSONDecodeError):
            text = body.decode("utf-8", errors="replace")
        return text.replace(self.config.api_key, "[REDACTED]")[:500]

    def _request(self, method: str, path: str, payload: dict | None = None) -> HttpResponse:
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        except UnicodeEncodeError as exc:
            raise InvalidResponse("The request contains invalid Unicode; retype the affected Terminal input") from exc
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.transport.send(method, url, self._headers(), body, self.config.timeout)
            except (ConnectionFailure, RequestTimeout) as exc:
                if attempt >= self.config.max_retries:
                    raise type(exc)(f"{exc} at {self.config.base_url}") from exc
                self.sleep(0.5 * (2**attempt))
                continue
            if (response.status == 429 or response.status >= 500) and attempt < self.config.max_retries:
                self.sleep(0.5 * (2**attempt))
                continue
            return response
        raise GeminiAPIError("Gemini request failed")

    def check_model(self) -> None:
        model = parse.quote(self.config.model, safe="")
        response = self._request("GET", f"models/{model}")
        if response.status == 404:
            raise ModelUnavailable(f"Gemini model is unavailable: {self.config.model}")
        if response.status != 200:
            raise GeminiAPIError(f"Gemini model check failed (HTTP {response.status}): {self._safe_detail(response.body)}")
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidResponse("Gemini returned an invalid model response") from exc
        if payload.get("name") != f"models/{self.config.model}":
            raise ModelUnavailable(f"Unexpected Gemini model response for {self.config.model}")
        methods = payload.get("supportedGenerationMethods", [])
        if methods and "generateContent" not in methods:
            raise ModelUnavailable(f"Model does not support generateContent: {self.config.model}")

    def chat(self, messages: list[dict[str, str]]) -> str:
        systems = [item["content"] for item in messages if item.get("role") == "system"]
        contents = []
        for item in messages:
            role = item.get("role")
            if role == "system":
                continue
            if role not in {"user", "assistant"}:
                raise InvalidResponse(f"Unsupported message role: {role}")
            contents.append({
                "role": "model" if role == "assistant" else "user",
                "parts": [{"text": item.get("content", "")}],
            })
        payload = {
            "systemInstruction": {"parts": [{"text": "\n\n".join(systems)}]},
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_output_tokens,
            },
            "store": False,
        }
        model = parse.quote(self.config.model, safe="")
        response = self._request("POST", f"models/{model}:generateContent", payload)
        if response.status != 200:
            detail = self._safe_detail(response.body)
            if response.status in {401, 403}:
                raise GeminiAPIError("Gemini authentication failed; verify GEMINI_API_KEY and its restrictions")
            if response.status == 429:
                raise GeminiAPIError("Gemini quota or rate limit was exceeded")
            raise GeminiAPIError(f"Gemini request failed (HTTP {response.status}): {detail}")
        try:
            result = json.loads(response.body.decode("utf-8"))
            candidates = result.get("candidates", [])
            if not candidates:
                reason = result.get("promptFeedback", {}).get("blockReason")
                if reason:
                    raise SafetyBlocked(f"Gemini blocked the prompt: {reason}")
                raise InvalidResponse("Gemini returned no answer candidate")
            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")
            parts = candidate.get("content", {}).get("parts", [])
            text_parts = [part["text"] for part in parts if isinstance(part, dict) and not part.get("thought") and isinstance(part.get("text"), str)]
            answer = "".join(text_parts).strip()
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise InvalidResponse("Gemini returned an invalid response") from exc
        if not answer:
            if finish_reason in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "ESCALATION"}:
                raise SafetyBlocked(f"Gemini blocked the response: {finish_reason}")
            raise InvalidResponse(f"Gemini returned an empty answer (finish reason: {finish_reason or 'unknown'})")
        if "<think>" in answer.lower() or "</think>" in answer.lower():
            raise InvalidResponse("Gemini mixed hidden reasoning into the final answer")
        return answer
