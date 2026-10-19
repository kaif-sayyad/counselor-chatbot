import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

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
    def test_gemini_call_payload_and_system_prompt(self, mock_post):
        """Verify prompt structure sent to Gemini contains all mandatory rules."""
        import api.index as idx
        orig_key = idx.GEMINI_API_KEY
        try:
            idx.GEMINI_API_KEY = "test_dummy_key"
            
            # Setup mock response from Gemini
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Vocational courses provide hands-on experience and apprenticeship opportunities. If your son does not find immediate placement, he can explore lateral entry into a Diploma or consult our human counsellor for local openings."
                                }
                            ]
                        },
                        "finishReason": "STOP"
                    }
                ]
            }
            mock_post.return_value = mock_resp

            payload = {
                "message": "What if my son does not get a job after the course?",
                "language": "en",
                "context": {
                    "trade": "Electrician",
                    "location": "Nagpur"
                }
            }

            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("Vocational courses provide hands-on experience", data["reply"])
            self.assertTrue(data.get("suggest_counsellor"))

            # Inspect what was sent to requests.post
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            req_json = called_kwargs.get("json", {})
            sys_inst = req_json.get("system_instruction", {}).get("parts", [{}])[0].get("text", "")
            
            # Verify system instruction contains all required rules
            self.assertIn("NO INVENTED NUMBERS", sys_inst)
            self.assertIn("Class 6 to 8 reading level", sys_inst)
            self.assertIn("NEVER say one pathway is better", sys_inst)
            self.assertIn("PROMPT INJECTION DEFENSE", sys_inst)
            self.assertIn("Electrician", sys_inst)
            self.assertIn("Nagpur", sys_inst)
            self.assertIn("VERIFIED KNOWLEDGE BASE", sys_inst)

        finally:
            idx.GEMINI_API_KEY = orig_key

    @patch("requests.post")
    def test_marathi_chat_flow(self, mock_post):
        """Verify Marathi request sends Marathi instruction and returns Marathi response."""
        import api.index as idx
        orig_key = idx.GEMINI_API_KEY
        try:
            idx.GEMINI_API_KEY = "test_dummy_key"

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "आयटीआय नंतर तंत्रनिकेतन (पॉलिटेक्निक) डिप्लोमाच्या दुसऱ्या वर्षात थेट प्रवेश (Lateral Entry) मिळतो. अधिक मदतीसाठी मानवी समुपदेशकांशी बोला."
                                }
                            ]
                        },
                        "finishReason": "STOP"
                    }
                ]
            }
            mock_post.return_value = mock_resp

            payload = {
                "message": "आयटीआय नंतर पुढील शिक्षण घेता येते का?",
                "language": "mr",
                "context": {
                    "trade": "Fitter"
                }
            }

            res = self.client.post("/api/chat", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("थेट प्रवेश", data["reply"])
            self.assertTrue(data.get("suggest_counsellor"))

            # Check that Marathi system instruction was passed
            called_args, called_kwargs = mock_post.call_args
            req_json = called_kwargs.get("json", {})
            sys_inst = req_json.get("system_instruction", {}).get("parts", [{}])[0].get("text", "")
            self.assertIn("Marathi", sys_inst)

        finally:
            idx.GEMINI_API_KEY = orig_key

    @patch("requests.post")
    def test_safety_blocked_response(self, mock_post):
        """When Gemini returns finishReason: SAFETY, returns safe fallback and counsellor offer."""
        import api.index as idx
        orig_key = idx.GEMINI_API_KEY
        try:
            idx.GEMINI_API_KEY = "test_dummy_key"

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "candidates": [
                    {
                        "content": {"parts": []},
                        "finishReason": "SAFETY"
                    }
                ]
            }
            mock_post.return_value = mock_resp

            res = self.client.post("/api/chat", json={"message": "unsafe test"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("safety policies", data["reply"])
            self.assertTrue(data["suggest_counsellor"])

        finally:
            idx.GEMINI_API_KEY = orig_key


if __name__ == "__main__":
    unittest.main()
