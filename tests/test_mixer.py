import asyncio
import os
import unittest
from unittest.mock import patch, AsyncMock

from xparallel import mixer


class MixerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "XP_MIXER_ENABLED": "1",
            "XP_MIXER_TIMEOUT": "2",
            "XP_MIXER_MAX_MODELS": "4",
            "ANTHROPIC_API_KEY": "test-a",
            "OPENAI_API_KEY": "test-o",
            "GOOGLE_API_KEY": "test-g",
            "MOONSHOT_API_KEY": "test-m",
        }, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()

    async def test_parallel_fanout(self):
        entries = [{"provider": str(i), "model_id": str(i), "env_key": "OPENAI_API_KEY", "api_base": "x"} for i in range(4)]
        active = 0
        peak = 0
        lock = asyncio.Lock()
        async def fake(entry, prompt, context=""):
            nonlocal active, peak
            async with lock:
                active += 1
                peak = max(peak, active)
            await asyncio.sleep(.03)
            async with lock:
                active -= 1
            return {"provider": entry["provider"], "model_id": entry["model_id"], "text": "ok", "latency_ms": 30, "tokens_in": 1, "tokens_out": 1, "response_hash": "h", "error": None}
        with patch.object(mixer, "model_registry", return_value=entries), patch.object(mixer, "call_provider", new=fake), patch.object(mixer, "_synthesize", new=AsyncMock(return_value=("done", {"provider":"0","model_id":"0"}))):
            result = await mixer.mix("question")
        self.assertEqual(result["state"], "ok")
        self.assertGreater(peak, 1)

    async def test_one_provider_failure_isolated(self):
        entries = [{"provider":"a","model_id":"a","env_key":"ANTHROPIC_API_KEY","api_base":"x"},{"provider":"b","model_id":"b","env_key":"OPENAI_API_KEY","api_base":"x"}]
        async def fake(entry, prompt, context=""):
            return {"provider":entry["provider"],"model_id":entry["model_id"],"text":"" if entry["provider"]=="a" else "answer","latency_ms":1,"tokens_in":None,"tokens_out":None,"response_hash":None,"error":"provider_failed" if entry["provider"]=="a" else None}
        with patch.object(mixer, "model_registry", return_value=entries), patch.object(mixer, "call_provider", new=fake), patch.object(mixer, "_synthesize", new=AsyncMock(return_value=("final", {"provider":"b","model_id":"b"}))):
            result = await mixer.mix("question")
        self.assertEqual(result["state"], "ok")
        self.assertTrue(any(x["reason"]=="provider_failed" for x in result["skipped"]))

    async def test_zero_configured_returns_unavailable(self):
        for key in ("ANTHROPIC_API_KEY","OPENAI_API_KEY","GOOGLE_API_KEY","MOONSHOT_API_KEY"):
            os.environ.pop(key, None)
        with patch.object(mixer, "model_registry", return_value=mixer.DEFAULTS):
            result = await mixer.mix("question")
        self.assertEqual(result["state"], "mixer_unavailable")

    async def test_retired_id_is_config_error(self):
        os.environ["XP_MIXER_MODELS_JSON"] = '[{"provider":"google","model_id":"gemini-2.0-flash","env_key":"GOOGLE_API_KEY","api_base":"x"}]'
        with self.assertRaises(mixer.MixerConfigError):
            mixer.model_registry()

    async def test_synthesis_prompt_contains_all_answers(self):
        entries = [{"provider":"openai","model_id":"gpt-4o","env_key":"OPENAI_API_KEY","api_base":"x"}]
        seen = {}
        async def fake(entry, prompt, context=""):
            seen["prompt"] = prompt
            return {"provider":"openai","model_id":"gpt-4o","text":"final","latency_ms":1,"tokens_in":1,"tokens_out":1,"response_hash":"h","error":None}
        with patch.object(mixer, "call_provider", new=fake):
            text, meta = await mixer._synthesize("q", [{"provider":"a","model_id":"a1","text":"ANSWER_A"},{"provider":"b","model_id":"b1","text":"ANSWER_B"}], entries, 2)
        self.assertIn("ANSWER_A", seen["prompt"])
        self.assertIn("ANSWER_B", seen["prompt"])
        self.assertEqual(text, "final")

    async def test_selected_plugin_context_is_passed_to_provider_calls(self):
        entries = [{"provider":"openai","model_id":"gpt-4o","env_key":"OPENAI_API_KEY","api_base":"x"}]
        seen = {}
        async def fake(entry, prompt, context=""):
            seen["context"] = context
            return {"provider":"openai","model_id":"gpt-4o","text":"answer","latency_ms":1,"tokens_in":1,"tokens_out":1,"response_hash":"h","error":None}
        with patch.object(mixer, "model_registry", return_value=entries), \
             patch("xparallel.plugins.retrieve_plugin_context", return_value={"context":"retrieved-source-snippet","results":[{"plugin_id":"web_search","state":"ok"}]}), \
             patch.object(mixer, "call_provider", new=fake), \
             patch.object(mixer, "_synthesize", new=AsyncMock(return_value=("final", {"provider":"openai","model_id":"gpt-4o"}))):
            result = await mixer.mix("question", plugin_ids=["web_search"])
        self.assertEqual(result["state"], "ok")
        self.assertIn("retrieved-source-snippet", seen["context"])
        self.assertEqual(result["plugin_results"][0]["plugin_id"], "web_search")

    async def test_timeout_budget_is_enforced(self):
        entries = [{"provider":"openai","model_id":"gpt-4o","env_key":"OPENAI_API_KEY","api_base":"x"}]
        async def slow(entry, prompt, context=""):
            await asyncio.sleep(.2)
            return {"provider":"openai","model_id":"gpt-4o","text":"late","latency_ms":200,"tokens_in":1,"tokens_out":1,"response_hash":"h","error":None}
        with patch.dict(os.environ, {"XP_MIXER_TIMEOUT":"0.02"}), patch.object(mixer, "model_registry", return_value=entries), patch.object(mixer, "call_provider", new=slow):
            result = await mixer.mix("question")
        self.assertIn(result["state"], ("mixer_unavailable", "synthesis_failed"))
        self.assertTrue(any(x["reason"]=="request_timeout_budget_exceeded" for x in result["skipped"]))


if __name__ == "__main__":
    unittest.main()
