import unittest

from tools.security_chatbot.cli import run_repl
from tools.security_chatbot.config import GeminiConfig
from tools.security_chatbot.session import ChatSession


class FakeClient:
    def chat(self, messages):
        return "Trả lời từ mock"


class CliTests(unittest.TestCase):
    def test_commands_and_repeated_questions(self):
        inputs = iter(["/help", "câu một", "/clear", "câu hai", "/exit"])
        outputs = []
        session = ChatSession(GeminiConfig(api_key="test"), FakeClient())
        run_repl(session, lambda _: next(inputs), outputs.append)
        self.assertEqual(outputs.count("Trả lời từ mock"), 2)
        self.assertEqual(outputs.count("Waiting for Gemini..."), 2)
        self.assertIn("Conversation history cleared.", outputs)
        self.assertIn("Goodbye.", outputs)


if __name__ == "__main__":
    unittest.main()
