import hashlib
import json
import os
import unittest
from unittest.mock import patch

from xparallel import mixer


class MixerConfigTests(unittest.TestCase):
    def test_missing_model_configuration_is_empty_not_fabricated(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mixer.model_registry(), [])

    def test_invalid_provider_is_rejected(self):
        raw = json.dumps([{"provider": "unknown", "model_id": "x"}])
        with patch.dict(os.environ, {"XP_MIXER_MODELS_JSON": raw}, clear=True):
            with self.assertRaises(mixer.MixerConfigError):
                mixer.model_registry()

    def test_model_id_is_required_and_endpoint_host_is_restricted(self):
        with patch.dict(os.environ, {"XP_MIXER_MODELS_JSON": json.dumps([
            {"provider": "openai", "model_id": "gpt-configured", "api_base": "https://example.com/v1/chat/completions"}
        ])}, clear=True):
            with self.assertRaises(mixer.MixerConfigError):
                mixer.model_registry()

    def test_duplicate_provider_family_is_rejected(self):
        raw = json.dumps([
            {"provider": "openai", "model_id": "model-a"},
            {"provider": "openai", "model_id": "model-b"},
        ])
        with patch.dict(os.environ, {"XP_MIXER_MODELS_JSON": raw}, clear=True):
            with self.assertRaises(mixer.MixerConfigError):
                mixer.model_registry()

    def test_no_provider_keys_returns_explicit_unavailable(self):
        with patch.dict(os.environ, {
            "XP_MIXER_MODELS_JSON": json.dumps([
                {"provider": "openai", "model_id": "model-a"},
                {"provider": "moonshot", "model_id": "model-b"},
            ])
        }, clear=True):
            import asyncio
            result = asyncio.run(mixer.mix("hello"))
        self.assertEqual(result["state"], "mixer_unavailable")
        self.assertEqual(result["final_answer"], "")
        self.assertTrue(result["skipped"])

    def test_successful_provider_response_has_hash_and_reported_usage(self):
        fake = {"choices": [{"message": {"content": "answer"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4}}
        entry = {"provider": "openai", "model_id": "configured-model", "env_key": "OPENAI_API_KEY",
                 "api_base": "https://api.openai.com/v1/chat/completions",
                 "max_tokens": 100, "timeout_seconds": 2}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "not-a-real-test-key"}, clear=True), \
             patch.object(mixer, "_bounded_post", return_value=fake):
            result = mixer._call(entry, "question", "system")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_tokens"], 12)
        self.assertEqual(result["output_tokens"], 4)
        self.assertEqual(result["response_hash"], hashlib.sha256(b"answer").hexdigest())
        self.assertEqual(result["usage_kind"], "provider_reported")

    def test_provider_error_does_not_return_secret_or_response_body(self):
        entry = {"provider": "openai", "model_id": "configured-model", "env_key": "OPENAI_API_KEY",
                 "api_base": "https://api.openai.com/v1/chat/completions",
                 "max_tokens": 100, "timeout_seconds": 2}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret-value"}, clear=True), \
             patch.object(mixer, "_bounded_post", side_effect=RuntimeError("provider_http_401")):
            result = mixer._call(entry, "question", "system")
        self.assertEqual(result["status"], "error")
        self.assertNotIn("secret-value", json.dumps(result))
        self.assertEqual(result["error"], "provider_http_401")


if __name__ == "__main__":
    unittest.main()
