import unittest
import json
import os
import sys

# Ensure api directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app, build_system_instruction, check_rate_limit, _ip_requests


class TestSkillPathChatbot(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check_unconfigured(self):
        """GET /api/health returns configured: False when key is unset, without leaking keys."""
        with app.app_context():
            res = self.client.get("/api/health")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("configured", data)
            self.assertIn("model", data)
            # Ensure no secret keys in payload
            self.assertNotIn("key", json.dumps(data).lower())
            self.assertNotIn("api_key", data)

    def test_static_routes(self):
        """Verify GET / serves index.html and static assets are accessible."""
        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn(b"SkillPath AI Counsellor", res_index.data)

        res_css = self.client.get("/style.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn(b"--color-primary", res_css.data)

        res_js = self.client.get("/app.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertIn(b"SkillPath AI Counsellor", res_js.data)

    def test_security_headers(self):
        """Verify CSP frame-ancestors is present and X-Frame-Options is NOT DENY."""
        res = self.client.get("/")
        csp = res.headers.get("Content-Security-Policy", "")
        self.assertIn("frame-ancestors", csp)
        x_frame = res.headers.get("X-Frame-Options", "")
        self.assertNotEqual(x_frame.upper(), "DENY")

    def test_cors_headers(self):
        """Verify CORS headers on /api/* endpoints."""
        res = self.client.options(
            "/api/chat",
            headers={"Origin": "https://example.com"}
        )
        self.assertEqual(res.status_code, 204)
        self.assertIn("Access-Control-Allow-Methods", res.headers)

    def test_chat_unconfigured_key_english(self):
        """When key is not set, POST /api/chat returns friendly English guidance."""
        # Ensure GEMINI_API_KEY is empty for this test
        import api.index as idx_module
        old_key = idx_module.GEMINI_API_KEY
        try:
            idx_module.GEMINI_API_KEY = ""
            payload = {
                "message": "What is ITI course?",
                "language": "en"
            }
            res = self.client.post(
                "/api/chat",
                data=json.dumps(payload),
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertFalse(data.get("configured", True))
            self.assertIn("not configured", data["reply"])
            self.assertTrue(data.get("suggest_counsellor"))
        finally:
            idx_module.GEMINI_API_KEY = old_key

    def test_chat_unconfigured_key_marathi(self):
        """When key is not set and language is mr, returns friendly Marathi guidance."""
        import api.index as idx_module
        old_key = idx_module.GEMINI_API_KEY
        try:
            idx_module.GEMINI_API_KEY = ""
            payload = {
                "message": "इलेक्ट्रिशियन कोर्सबद्दल माहिती द्या",
                "language": "mr"
            }
            res = self.client.post(
                "/api/chat",
                data=json.dumps(payload),
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertFalse(data.get("configured", True))
            self.assertIn("कॉन्फिगर केलेली नाही", data["reply"])
            self.assertTrue(data.get("suggest_counsellor"))
        finally:
            idx_module.GEMINI_API_KEY = old_key

    def test_message_validation(self):
        """Empty message should return 400."""
        res = self.client.post(
            "/api/chat",
            data=json.dumps({"message": "   "}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)

    def test_rate_limiting(self):
        """Exceeding RATE_LIMIT_MAX requests within window triggers 429."""
        _ip_requests["test_ip_123"].clear()
        for i in range(25):
            allowed = check_rate_limit("test_ip_123")
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
        # 26th request should fail
        exceeded = check_rate_limit("test_ip_123")
        self.assertFalse(exceeded, "26th request should be rate limited")

    def test_system_prompt_builder(self):
        """Verify prompt construction contains critical rules and verified facts."""
        prompt_en = build_system_instruction(language="en", trade="Electrician", location="Nagpur")
        self.assertIn("SkillPath AI Counsellor", prompt_en)
        self.assertIn("NO INVENTED NUMBERS", prompt_en)
        self.assertIn("Electrician", prompt_en)
        self.assertIn("Nagpur", prompt_en)
        self.assertIn("VERIFIED KNOWLEDGE BASE", prompt_en)
        self.assertIn("NSQF", prompt_en)

        prompt_mr = build_system_instruction(language="mr")
        self.assertIn("Marathi", prompt_mr)


if __name__ == "__main__":
    unittest.main()
