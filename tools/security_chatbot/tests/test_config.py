from pathlib import Path
import tempfile
import unittest

from tools.security_chatbot.config import ConfigError, DEFAULT_MODEL, GeminiConfig


class ConfigTests(unittest.TestCase):
    def test_defaults_and_key(self):
        config = GeminiConfig.from_env({"GEMINI_API_KEY": "test-key"})
        self.assertEqual(config.model, DEFAULT_MODEL)
        self.assertEqual(config.api_key, "test-key")

    def test_environment_overrides_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("GEMINI_API_KEY=file-key\nGEMINI_MAX_TURNS=2\n", encoding="utf-8")
            config = GeminiConfig.from_env({"GEMINI_API_KEY": "process-key"}, path)
        self.assertEqual(config.api_key, "process-key")
        self.assertEqual(config.max_turns, 2)

    def test_key_and_https_are_required(self):
        with self.assertRaisesRegex(ConfigError, "GEMINI_API_KEY"):
            GeminiConfig.from_env({})
        with self.assertRaises(ConfigError):
            GeminiConfig(api_key="key", base_url="http://example.com").validate()


if __name__ == "__main__":
    unittest.main()
