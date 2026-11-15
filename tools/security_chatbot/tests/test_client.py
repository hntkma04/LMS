import json
import unittest

from tools.security_chatbot.client import (
    ConnectionFailure,
    GeminiAPIError,
    GeminiClient,
    HttpResponse,
    InvalidResponse,
    ModelUnavailable,
    RequestTimeout,
    SafetyBlocked,
)
from tools.security_chatbot.config import GeminiConfig


class FakeTransport:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def send(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def response(status, payload):
    return HttpResponse(status, json.dumps(payload).encode("utf-8"))


class ClientTests(unittest.TestCase):
    def config(self, **kwargs):
        return GeminiConfig(api_key="test-secret", max_retries=0, **kwargs).validate()

    def test_model_check(self):
        transport = FakeTransport([response(200, {
            "name": "models/gemini-3.8-flash",
            "supportedGenerationMethods": ["generateContent"],
        })])
        GeminiClient(self.config(), transport).check_model()
        self.assertTrue(transport.calls[0][1].endswith("/models/gemini-3.8-flash"))

    def test_model_mismatch(self):
        client = GeminiClient(self.config(), FakeTransport([response(404, {"error": {"message": "not found"}})]))
        with self.assertRaises(ModelUnavailable):
            client.check_model()

    def test_payload_roles_system_prompt_and_thought_filter(self):
        transport = FakeTransport([response(200, {"candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [
                {"text": "private reasoning", "thought": True},
                {"text": "Câu trả lời an toàn"},
            ]},
        }]})])
        client = GeminiClient(self.config(), transport)
        result = client.chat([
            {"role": "system", "content": "trusted rules"},
            {"role": "user", "content": "xin chào"},
            {"role": "assistant", "content": "chào bạn"},
            {"role": "user", "content": "tiếp tục"},
        ])
        self.assertEqual(result, "Câu trả lời an toàn")
        payload = json.loads(transport.calls[0][3].decode("utf-8"))
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "trusted rules")
        self.assertEqual([item["role"] for item in payload["contents"]], ["user", "model", "user"])
        self.assertFalse(payload["store"])
        self.assertEqual(transport.calls[0][2]["x-goog-api-key"], "test-secret")

    def test_retries_transient_error(self):
        transport = FakeTransport([
            response(503, {"error": {"message": "busy"}}),
            response(200, {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}),
        ])
        config = GeminiConfig(api_key="key", max_retries=1).validate()
        client = GeminiClient(config, transport, sleep=lambda _: None)
        self.assertEqual(client.chat([{"role": "user", "content": "test"}]), "ok")
        self.assertEqual(len(transport.calls), 2)

    def test_auth_error_does_not_leak_key(self):
        client = GeminiClient(self.config(), FakeTransport([
            response(403, {"error": {"message": "invalid test-secret"}})
        ]))
        with self.assertRaises(GeminiAPIError) as caught:
            client.chat([{"role": "user", "content": "test"}])
        self.assertNotIn("test-secret", str(caught.exception))

    def test_safety_block_and_invalid_response(self):
        blocked = GeminiClient(self.config(), FakeTransport([
            response(200, {"promptFeedback": {"blockReason": "SAFETY"}})
        ]))
        with self.assertRaises(SafetyBlocked):
            blocked.chat([])
        invalid = GeminiClient(self.config(), FakeTransport([response(200, {"candidates": []})]))
        with self.assertRaises(InvalidResponse):
            invalid.chat([])

    def test_connection_and_timeout_errors(self):
        for failure in (ConnectionFailure("offline"), RequestTimeout("slow")):
            with self.subTest(failure=type(failure).__name__):
                client = GeminiClient(self.config(), FakeTransport([failure]))
                with self.assertRaises(type(failure)):
                    client.chat([])

    def test_invalid_unicode_is_reported_without_transport_call(self):
        transport = FakeTransport([])
        client = GeminiClient(self.config(), transport)
        with self.assertRaisesRegex(InvalidResponse, "invalid Unicode"):
            client.chat([{"role": "user", "content": "bad\udcc6input"}])
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
