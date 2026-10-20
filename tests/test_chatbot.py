import unittest
import json
import os
import sys

# Ensure api directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app, build_system_instruction, check_rate_limit, _ip_requests, extract_numbers, validate_number_guard


class TestSkillPathChatbot(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check_unconfigured(self):
        """GET /api/health returns mode 'offline' and configured: False when key is unset, without leaking keys."""
        import api.index as idx_module
        old_key = idx_module.GROQ_API_KEY
        try:
            idx_module.GROQ_API_KEY = ""
            with app.app_context():
                res = self.client.get("/api/health")
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["status"], "ok")
                self.assertEqual(data["mode"], "offline")
                self.assertFalse(data["configured"])
                self.assertEqual(data["model"], "qwen/qwen3-32b")
                # Ensure no secret keys in payload
                self.assertNotIn("key", json.dumps(data).lower())
                self.assertNotIn("api_key", data)
        finally:
            idx_module.GROQ_API_KEY = old_key

    def test_health_check_configured(self):
        """GET /api/health returns mode 'groq' and configured: True when key is set."""
        import api.index as idx_module
        old_key = idx_module.GROQ_API_KEY
        try:
            idx_module.GROQ_API_KEY = "gsk_test_mock_key_12345"
            with app.app_context():
                res = self.client.get("/api/health")
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["mode"], "groq")
                self.assertTrue(data["configured"])
                self.assertNotIn("gsk_test", json.dumps(data))
        finally:
            idx_module.GROQ_API_KEY = old_key

    def test_static_routes(self):
        """Verify GET / serves index.html and static assets are accessible."""
        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn(b"SkillPath AI Counsellor", res_index.data)
        self.assertIn(b"header-badge", res_index.data)

        res_css = self.client.get("/style.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn(b"--color-primary", res_css.data)
        self.assertIn(b"badge-groq", res_css.data)

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

    def test_chat_unconfigured_key_returns_local_answer(self):
        """When key is not set, POST /api/chat returns relatable local answer with HTTP 200 and mode 'basic'."""
        import api.index as idx_module
        old_key = idx_module.GROQ_API_KEY
        try:
            idx_module.GROQ_API_KEY = ""
            payload = {
                "message": "What is the starting income after ITI?",
                "language": "en"
            }
            res = self.client.post(
                "/api/chat",
                data=json.dumps(payload),
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("mode"), "basic")
            self.assertFalse(data.get("configured", True))
            self.assertTrue(len(data["reply"]) > 20)
            self.assertTrue(data.get("suggest_counsellor"))
        finally:
            idx_module.GROQ_API_KEY = old_key

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

    def test_number_guard_helpers(self):
        """Verify number extraction and guard logic."""
        nums = extract_numbers("NSQF Level 4 course with 2 years duration and १२ वीं")
        self.assertIn("4", nums)
        self.assertIn("2", nums)
        self.assertIn("12", nums)

        allowed = {"1", "2", "3", "4", "10", "12"}
        self.assertTrue(validate_number_guard("Course has 2 years duration at level 4", allowed))
        # An invented number not in allowed set (e.g. 25000)
        self.assertFalse(validate_number_guard("Salary will be 25000 rupees", allowed))


if __name__ == "__main__":
    unittest.main()
