import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.test import SimpleTestCase, override_settings

from identity_management import IdentityClient, IdentityFailure


CONFIG = {"DISCOVERY_ENABLED": False, "BASE_URL": "http://identity.test:8001",
          "TIMEOUT_SECONDS": 0.5, "SERVICE_TOKEN": "test-only-secret"}
PROFILE = {"user_id": "SV01", "first_name": "An", "last_name": "Nguyen", "gender": None,
           "date_of_birth": None, "email": "an@example.com", "phone": "123", "role": 3,
           "status": 1, "created_at": None, "updated_at": None}


@override_settings(IDENTITY_MANAGEMENT_CLIENT=CONFIG)
class IdentityClientTests(SimpleTestCase):
    def setUp(self):
        self.client = IdentityClient()
        self.request = SimpleNamespace(headers={"Authorization": "Bearer caller", "X-Request-ID": "request-123"})
        self.opener = patch("identity_management.build_opener")
        self.open = self.opener.start().return_value.open
        self.addCleanup(self.opener.stop)
        self.response = self.open.return_value.__enter__.return_value
        self.response.status = 200
        self.response.read.return_value = json.dumps(PROFILE).encode()

    def call(self, method="GET", **kwargs):
        return self.client.call(self.request, "students", method, **kwargs)

    def test_contract_headers_no_password_and_bounded_timeout(self):
        self.assertEqual(self.call(user_id="SV01"), PROFILE)
        request = self.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://identity.test:8001/internal/v1/identities/students/SV01/")
        self.assertEqual(request.get_header("Authorization"), "Bearer caller")
        self.assertEqual(request.get_header("X-service-token"), "test-only-secret")
        self.assertEqual(request.get_header("X-request-id"), "request-123")
        self.assertEqual(self.open.call_args.kwargs["timeout"], 0.5)
        self.response.status = 201
        self.call("POST", data={"user_id": "SV01", "password": "new-password"})
        self.assertEqual(json.loads(self.open.call_args.args[0].data)["password"], "new-password")

    def test_sensitive_or_wrong_role_malformed_and_oversized_response_rejected(self):
        for body in [json.dumps({**PROFILE, "password": "secret"}).encode(),
                     json.dumps({**PROFILE, "role": 1}).encode(), b"[]", b"not json", b"x" * 262145]:
            self.client = IdentityClient()
            self.response.read.return_value = body
            with self.assertRaises(IdentityFailure):
                self.call(user_id="SV01")

    def test_write_timeout_is_uncertain_no_replay_and_circuit_opens(self):
        self.open.side_effect = TimeoutError()
        for _ in range(3):
            with self.assertRaises(IdentityFailure) as caught:
                self.call("PATCH", user_id="SV01", data={"email": "new@example.com"})
            self.assertTrue(caught.exception.uncertain)
        with self.assertRaises(IdentityFailure) as caught:
            self.call("DELETE", user_id="SV01")
        self.assertFalse(caught.exception.uncertain)
        self.assertEqual(self.open.call_count, 3)

    def test_expected_http_rejection_is_confirmed_and_safe(self):
        for status, mapped in [(400, 400), (401, 503), (403, 503), (404, 404), (409, 409), (429, 503)]:
            self.open.side_effect = HTTPError("http://identity.test", status, "private", {}, None)
            with self.assertRaises(IdentityFailure) as caught:
                self.call("PATCH", user_id="SV01", data={})
            self.assertFalse(caught.exception.uncertain)
            self.assertEqual(caught.exception.status_code, mapped)
            self.assertNotIn("private", str(caught.exception))
        self.open.side_effect = HTTPError("http://identity.test", 503, "private", {}, None)
        with self.assertRaises(IdentityFailure) as caught:
            self.call("DELETE", user_id="SV01")
        self.assertTrue(caught.exception.uncertain)

    @patch("LectureManager.identity_client.fetch_json", side_effect=TimeoutError())
    def test_discovery_failure_precedes_write_and_has_no_static_fallback(self, lookup):
        with override_settings(IDENTITY_MANAGEMENT_CLIENT={**CONFIG, "DISCOVERY_ENABLED": True}):
            with self.assertRaises(IdentityFailure) as caught:
                self.call("POST", data={"user_id": "SV01"})
        self.assertFalse(caught.exception.uncertain)
        self.open.assert_not_called()

    def test_batch_and_delete_contracts(self):
        self.response.read.return_value = json.dumps({"users": {"SV01": PROFILE, "missing": None}}).encode()
        result = self.call("POST", data={"user_ids": ["SV01", "missing"]}, batch=True)
        self.assertIsNone(result["missing"])
        self.assertIn("/identity-profiles/students/", self.open.call_args.args[0].full_url)
        self.response.status = 204
        self.response.read.return_value = b""
        self.assertIsNone(self.call("DELETE", user_id="SV01"))

    def test_redirects_and_unexpected_status_are_uncertain_writes(self):
        self.open.side_effect = HTTPError("http://identity.test", 302, "redirect", {}, None)
        with self.assertRaises(IdentityFailure) as caught:
            self.call("POST", data={"user_id": "SV01"})
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(self.open.call_count, 1)
