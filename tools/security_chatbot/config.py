"""Environment and CLI configuration for Gemini."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class ConfigError(ValueError):
    pass


def load_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    result: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"Invalid environment entry at {path}:{line_number}")
        key, value = (part.strip() for part in line.split("=", 1))
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        result[key] = value
    return result


def _value(source: Mapping[str, str], key: str, converter, default):
    raw = source.get(key)
    if raw in (None, ""):
        return default
    try:
        return converter(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{key} has an invalid value") from exc


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.2
    max_output_tokens: int = 512
    timeout: float = 30.0
    max_turns: int = 8
    max_retries: int = 0

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        env_file: Path | None = None,
    ) -> "GeminiConfig":
        process_env = dict(os.environ if env is None else env)
        source = {**load_env_file(env_file), **process_env}
        config = cls(
            api_key=source.get("GEMINI_API_KEY", source.get("GOOGLE_API_KEY", "")),
            model=source.get("GEMINI_MODEL", DEFAULT_MODEL),
            base_url=source.get("GEMINI_BASE_URL", DEFAULT_BASE_URL),
            temperature=_value(source, "GEMINI_TEMPERATURE", float, 0.2),
            max_output_tokens=_value(source, "GEMINI_MAX_OUTPUT_TOKENS", int, 512),
            timeout=_value(source, "GEMINI_TIMEOUT_SECONDS", float, 30.0),
            max_turns=_value(source, "GEMINI_MAX_TURNS", int, 8),
            max_retries=_value(source, "GEMINI_MAX_RETRIES", int, 0),
        )
        return config.validate()

    def with_overrides(self, **values) -> "GeminiConfig":
        filtered = {key: value for key, value in values.items() if value is not None}
        return replace(self, **filtered).validate()

    def validate(self) -> "GeminiConfig":
        if not self.api_key or self.api_key == "EMPTY":
            raise ConfigError("GEMINI_API_KEY is required")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ConfigError("GEMINI_BASE_URL must be a valid HTTPS URL")
        if parsed.username or parsed.password:
            raise ConfigError("GEMINI_BASE_URL must not contain credentials")
        if not self.model.strip() or "/" in self.model or "\\" in self.model:
            raise ConfigError("GEMINI_MODEL has an invalid value")
        if not 0 <= self.temperature <= 2:
            raise ConfigError("GEMINI_TEMPERATURE must be between 0 and 2")
        if self.max_output_tokens <= 0 or self.timeout <= 0 or self.max_turns <= 0:
            raise ConfigError("Token, timeout, and history limits must be positive")
        if not 0 <= self.max_retries <= 5:
            raise ConfigError("GEMINI_MAX_RETRIES must be between 0 and 5")
        return replace(self, base_url=self.base_url.rstrip("/"))

    def public_summary(self) -> str:
        return f"provider=Gemini, model={self.model}, endpoint={self.base_url}"
