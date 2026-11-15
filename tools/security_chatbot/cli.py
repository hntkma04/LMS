"""Interactive Gemini chatbot for Terminal prompt testing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
import traceback
from typing import Callable, Sequence

from .client import ChatbotError, GeminiClient
from .config import ConfigError, GeminiConfig
from .session import ChatSession


HELP_TEXT = "Commands: /help (show commands), /clear (reset history), /exit (quit)"


def configure_terminal_encoding() -> None:
    """Avoid surrogateescape bytes from Windows/Docker interactive input."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gemini LMS security chatbot")
    parser.add_argument("--env-file", type=Path, default=Path("tools/security_chatbot/.env"))
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--max-turns", type=int)
    parser.add_argument("--skip-health-check", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser


def run_repl(
    session: ChatSession,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    output_fn("Gemini Security Assistant. Type /help for commands.")
    while True:
        try:
            text = input_fn("security> ").strip()
        except (EOFError, KeyboardInterrupt):
            output_fn("\nGoodbye.")
            return
        if not text:
            continue
        command = text.lower()
        if command == "/exit":
            output_fn("Goodbye.")
            return
        if command == "/help":
            output_fn(HELP_TEXT)
            continue
        if command == "/clear":
            session.clear()
            output_fn("Conversation history cleared.")
            continue
        try:
            output_fn("Waiting for Gemini...")
            started = time.monotonic()
            output_fn(session.ask(text))
            output_fn(f"[completed in {time.monotonic() - started:.1f}s]")
        except ChatbotError as exc:
            output_fn(f"Error: {exc}")


def main(argv: Sequence[str] | None = None) -> int:
    configure_terminal_encoding()
    args = build_parser().parse_args(argv)
    try:
        config = GeminiConfig.from_env(env_file=args.env_file).with_overrides(
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
            max_output_tokens=args.max_tokens,
            timeout=args.timeout,
            max_turns=args.max_turns,
        )
        client = GeminiClient(config)
        print(f"Starting {config.public_summary()}")
        print("Privacy notice: prompts and conversation history are sent to Google Gemini API.")
        if not args.skip_health_check:
            client.check_model()
        run_repl(ChatSession(config, client))
        return 0
    except (ConfigError, ChatbotError) as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        print("Check GEMINI_API_KEY, Internet access, API quota, and the configured model.", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
