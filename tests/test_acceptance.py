import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app, build_system_instruction


class TestAcceptanceCriteria(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_csp_with_allowed_origins(self):
        """When ALLOWED_ORIGINS is specified, frame-ancestors contains allowed origins."""
        import api.index as idx
        orig_origins = idx.ALLOWED_ORIGINS
        try:
            idx.ALLOWED_ORIGINS = ["https://main-skillpath-portal.vercel.app"]
            res = self.client.get("/")
            csp = res.headers.get("Content-Security-Policy", "")
            self.assertIn("frame-ancestors 'self' https://main-skillpath-portal.vercel.app", csp)
        finally:
            idx.ALLOWED_ORIGINS = orig_origins

    def test_csp_without_allowed_origins(self):
        """When ALLOWED_ORIGINS is empty, frame-ancestors is 'self'."""
        import api.index as idx
        orig_origins = idx.ALLOWED_ORIGINS
        try:
            idx.ALLOWED_ORIGINS = []
            res = self.client.get("/")
            csp = res.headers.get("Content-Security-Policy", "")
            self.assertEqual(csp, "frame-ancestors 'self';")
        finally:
            idx.ALLOWED_ORIGINS = orig_origins

    @patch("requests.post")
    def test_groq_success_strips_think_tags(self, mock_post):
        """1. Success returns the reply with no <think> text and verifies Groq payload."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_test_valid_key"

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "<think>Let me analyze the student's question and give a neutral answer.</think>Vocational education offers early practical skills and apprenticeships. Students can laterally enter diploma programs."
                        }
                    }
                ]
            }
            mock_post.return_value = mock_resp

            payload = {
                "message": "Tell me about vocational education.",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            # Verify <think>...</think> tags were completely stripped
            self.assertNotIn("<think>", data["reply"])
            self.assertNotIn("Let me analyze", data["reply"])
            self.assertIn("Vocational education offers early practical skills", data["reply"])
            self.assertEqual(data.get("mode"), "groq")

            # Verify Groq request structure
            mock_post.assert_called()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], "https://api.groq.com/openai/v1/chat/completions")
            req_headers = called_kwargs.get("headers", {})
            self.assertEqual(req_headers.get("Authorization"), "Bearer gsk_test_valid_key")

            req_json = called_kwargs.get("json", {})
            self.assertEqual(req_json.get("model"), "qwen/qwen3-32b")
            self.assertEqual(req_json.get("reasoning_format"), "hidden")
            self.assertEqual(req_json.get("temperature"), 0.6)
            self.assertEqual(req_json.get("top_p"), 0.95)
            self.assertEqual(req_json.get("max_completion_tokens"), 400)
        finally:
            idx.GROQ_API_KEY = orig_key

    @patch("requests.post")
    def test_timeout_fallback_to_local_answer(self, mock_post):
        """2. Timeout returns a local relatable answer with HTTP 200."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_test_valid_key"
            mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

            payload = {
                "message": "Is job security good after ITI?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            # Relatable fallback response received
            self.assertTrue(len(data.get("reply", "")) > 10)
            self.assertNotIn("Connection timed out", data.get("reply", ""))
            self.assertTrue(data.get("suggest_counsellor"))
            # Verified that retry was attempted (called twice)
            self.assertEqual(mock_post.call_count, 2)
        finally:
            idx.GROQ_API_KEY = orig_key

    @patch("requests.post")
    def test_http_429_rate_limit_fallback(self, mock_post):
        """3. Groq 429 returns a local relatable answer with HTTP 200."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_test_valid_key"
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.text = "Rate limit reached"
            mock_post.return_value = mock_resp

            payload = {
                "message": "What is the fee for Government ITI?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertTrue(len(data.get("reply", "")) > 15)
            self.assertNotIn("429", data.get("reply", ""))
        finally:
            idx.GROQ_API_KEY = orig_key

    @patch("requests.post")
    def test_http_401_auth_error_fallback(self, mock_post):
        """4. Groq 401 returns a local relatable answer with HTTP 200."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_invalid_key"
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Invalid API key"
            mock_post.return_value = mock_resp

            payload = {
                "message": "How does lateral entry to diploma work?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertTrue(len(data.get("reply", "")) > 15)
            self.assertNotIn("401", data.get("reply", ""))
        finally:
            idx.GROQ_API_KEY = orig_key

    @patch("requests.post")
    def test_invalid_json_fallback(self, mock_post):
        """5. Invalid JSON returns a local relatable answer with HTTP 200."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_test_valid_key"
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = ValueError("Corrupted JSON body")
            mock_post.return_value = mock_resp

            payload = {
                "message": "Can I get a job near my village?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertTrue(len(data.get("reply", "")) > 10)
        finally:
            idx.GROQ_API_KEY = orig_key

    def test_missing_key_returns_local_answers(self):
        """6. A missing key returns local answers with HTTP 200."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = ""
            payload = {
                "message": "How much can I earn as an electrician?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertFalse(data.get("configured", True))
            self.assertTrue(len(data.get("reply", "")) > 15)
        finally:
            idx.GROQ_API_KEY = orig_key

    def test_marathi_input_returns_marathi(self):
        """7. Marathi input returns Marathi from local fallback."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = ""
            payload = {
                "message": "आयटीआय नंतर नोकरीची हमी काय आहे?",
                "language": "mr"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            # Contains Marathi characters
            self.assertTrue(any('\u0900' <= char <= '\u097f' for char in data.get("reply", "")))
        finally:
            idx.GROQ_API_KEY = orig_key

    @patch("requests.post")
    def test_number_guard_rejects_unverified_number(self, mock_post):
        """8. A number not in the knowledge entries is rejected and falls back to local answer."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = "gsk_test_valid_key"

            # Mock Groq hallucinating an invented salary number (e.g. 45000) not in knowledge base
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "An electrician is guaranteed to earn 45000 rupees every month right after the course."
                        }
                    }
                ]
            }
            mock_post.return_value = mock_resp

            payload = {
                "message": "What is the income of an electrician?",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            # The hallucinated answer with 45000 must be discarded by number guard!
            self.assertNotIn("45000", data.get("reply", ""))
            # And replaced with the local safe answer in basic mode
            self.assertEqual(data.get("mode"), "basic")
        finally:
            idx.GROQ_API_KEY = orig_key

    def test_undetected_concern_shows_concern_chips(self):
        """When query matches neither FAQ nor 8 concerns, general friendly message and 8 chips are shown."""
        import api.index as idx
        orig_key = idx.GROQ_API_KEY
        try:
            idx.GROQ_API_KEY = ""
            payload = {
                "message": "xyz completely unrelated text 123456 qwerty",
                "language": "en"
            }
            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertIn("Thank you for asking. I want to give you a reliable answer", data.get("reply", ""))
            self.assertIsNotNone(data.get("chips"))
            self.assertEqual(len(data.get("chips")), 8)
        finally:
            idx.GROQ_API_KEY = orig_key


if __name__ == "__main__":
    unittest.main()
