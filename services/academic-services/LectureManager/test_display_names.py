from unittest.mock import patch
from urllib.error import HTTPError

from django.core.cache import cache
from django.db import OperationalError
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from MajorManager.models import Major
from . import identity_client as identity_module
from .display_names import ReaderLookupThrottle
from .models import Lecturer

CONFIG = {"DISCOVERY_ENABLED": False, "BASE_URL": "http://auth.test:8001",
          "TIMEOUT_SECONDS": 2, "SERVICE_TOKEN": "service-secret"}


class AcademicDisplayNamesTests(SimpleTestCase):
    url = "/api/v1/topic-display-names/"

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        token = AccessToken()
        token["user_id"] = "student"
        token["role"] = 3
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.major_patch = patch.object(Major.objects, "filter")
        self.lecturer_patch = patch.object(Lecturer.objects, "filter")
        self.identity_patch = patch.object(identity_module.identity_client, "names", return_value={"GV1": "Nguyen An"})
        self.majors = self.major_patch.start()
        self.lecturers = self.lecturer_patch.start()
        self.identity = self.identity_patch.start()
        self.addCleanup(self.major_patch.stop)
        self.addCleanup(self.lecturer_patch.stop)
        self.addCleanup(self.identity_patch.stop)
        self.majors.return_value.values_list.return_value = [("CNTT", "Information Technology")]
        self.lecturers.return_value.values_list.return_value = ["GV1"]
        self.payload = {"major_ids": ["CNTT", "missing", "CNTT"], "advisor_ids": ["GV1", "unknown"]}

    def post(self, payload=None):
        return self.client.post(self.url, self.payload if payload is None else payload, format="json")

    def test_authenticated_readers_get_batched_names(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"major_names": {"CNTT": "Information Technology", "missing": None},
                                         "advisor_names": {"GV1": "Nguyen An", "unknown": None}})
        self.majors.assert_called_once_with(pk__in=["CNTT", "missing"])
        self.lecturers.assert_called_once_with(pk__in=["GV1", "unknown"])
        self.identity.assert_called_once_with(["GV1"])
        self.majors.return_value.values_list.assert_called_once_with("major_id", "name")
        self.lecturers.return_value.values_list.assert_called_once_with("lecturer_id", flat=True)

    def test_missing_advisors_never_look_up_arbitrary_users(self):
        self.lecturers.return_value.values_list.return_value = []
        self.assertEqual(self.post().data["advisor_names"], {"GV1": None, "unknown": None})
        self.identity.assert_not_called()

    def test_identity_outage_keeps_major_names(self):
        self.identity.return_value = {"GV1": None}
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["major_names"]["CNTT"], "Information Technology")
        self.assertIsNone(response.data["advisor_names"]["GV1"])

    def test_auth_and_validation_fail_before_orm(self):
        for payload in ({}, {"major_ids": ["x"] * 101, "advisor_ids": []},
                        {"major_ids": [], "advisor_ids": [""]},
                        {"major_ids": [], "advisor_ids": [], "private": True},
                        {"major_ids": ["x" * 65537], "advisor_ids": []}):
            self.assertEqual(self.post(payload).status_code, 400)
        self.client.credentials()
        self.assertEqual(self.post().status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(self.post().status_code, 401)
        self.majors.assert_not_called()
        self.identity.assert_not_called()

    def test_storage_error_is_safe(self):
        self.majors.side_effect = OperationalError("private SQL")
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", str(response.data))

    def test_process_cache_rate_limit(self):
        with patch.object(ReaderLookupThrottle, "rate", "1/min"):
            self.assertEqual(self.post().status_code, 200)
            self.assertEqual(self.post().status_code, 429)


@override_settings(IDENTITY_NAMES_CLIENT=CONFIG)
class IdentityClientTests(SimpleTestCase):
    def setUp(self):
        self.client = identity_module.IdentityNamesClient()

    @patch.object(identity_module, "fetch_json", return_value={"names": {"GV1": "Nguyen An"}})
    def test_service_credential_and_deduplicated_batch(self, fetch):
        self.assertEqual(self.client.names(["GV1", "GV1"]), {"GV1": "Nguyen An"})
        fetch.assert_called_once_with("http://auth.test:8001/internal/v1/user-display-names/",
                                      {"X-Service-Token": "service-secret"}, 2, {"user_ids": ["GV1"]})
        self.assertNotIn("Authorization", fetch.call_args.args[1])

    @override_settings(IDENTITY_NAMES_CLIENT={**CONFIG, "BASE_URL": "http://127.0.0.1:8001"},
                       CONSUL={"URL": "http://unreachable-registry.invalid:8500", "TOKEN": "registry-secret"})
    @patch.object(identity_module, "fetch_json", return_value={"names": {"GV1": "Nguyen An"}})
    def test_explicit_loopback_names_do_not_use_discovery_or_caller_jwt(self, fetch):
        self.assertEqual(self.client.names(["GV1"]), {"GV1": "Nguyen An"})
        fetch.assert_called_once_with("http://127.0.0.1:8001/internal/v1/user-display-names/",
                                      {"X-Service-Token": "service-secret"}, 2, {"user_ids": ["GV1"]})

    @override_settings(IDENTITY_NAMES_CLIENT={**CONFIG, "BASE_URL": "http://127.0.0.1:8001"})
    @patch.object(identity_module, "fetch_json", side_effect=TimeoutError())
    def test_loopback_outage_still_returns_null_without_retry(self, fetch):
        self.assertEqual(self.client.names(["GV1"]), {"GV1": None})
        self.assertEqual(fetch.call_count, 1)

    @override_settings(IDENTITY_NAMES_CLIENT={**CONFIG, "DISCOVERY_ENABLED": True},
                       CONSUL={"URL": "http://registry:8500", "TOKEN": "consul-secret"})
    @patch.object(identity_module, "fetch_json")
    def test_discovery_and_separate_credentials(self, fetch):
        fetch.side_effect = [[{"Service": {"Service": "auth-service", "Address": "auth.local", "Port": 8001},
                               "Checks": [{"Status": "passing"}]}], {"names": {"GV1": "Nguyen An"}}]
        self.assertEqual(self.client.names(["GV1"])["GV1"], "Nguyen An")
        self.assertEqual(fetch.call_args_list[0].args, (
            "http://registry:8500/v1/health/service/auth-service?passing=true", {"X-Consul-Token": "consul-secret"}, 2))
        self.assertEqual(fetch.call_args_list[1].args[0], "http://auth.local:8001/internal/v1/user-display-names/")
        self.assertEqual(fetch.call_args_list[1].args[1], {"X-Service-Token": "service-secret"})

    @override_settings(IDENTITY_NAMES_CLIENT={**CONFIG, "DISCOVERY_ENABLED": True})
    @patch.object(identity_module, "fetch_json")
    def test_registry_failures_have_no_static_fallback(self, fetch):
        for payload in ([], {}, [{"Service": {}}],
                        [{"Service": {"Service": "auth-service", "Address": "bad/host", "Port": 8001},
                          "Checks": [{"Status": "passing"}]}],
                        [{"Service": {"Service": "auth-service"}, "Checks": [{"Status": "critical"}]}]):
            fetch.reset_mock()
            fetch.return_value = payload
            self.assertEqual(identity_module.IdentityNamesClient().names(["GV1"]), {"GV1": None})
            self.assertEqual(fetch.call_count, 1)

    @patch.object(identity_module, "fetch_json")
    def test_malformed_payload_missing_secret_and_empty(self, fetch):
        for payload in ({}, {"names": {}}, {"names": {"GV1": 5}}, {"names": {"GV1": "An", "extra": "Private"}}):
            fetch.return_value = payload
            self.assertEqual(identity_module.IdentityNamesClient().names(["GV1"]), {"GV1": None})
        fetch.reset_mock()
        self.assertEqual(self.client.names([]), {})
        with override_settings(IDENTITY_NAMES_CLIENT={**CONFIG, "SERVICE_TOKEN": ""}):
            self.assertEqual(self.client.names(["GV1"]), {"GV1": None})
        fetch.assert_not_called()

    @patch.object(identity_module, "fetch_json")
    def test_upstream_errors_return_null_without_leaking_details(self, fetch):
        for code in (401, 403, 404, 429, 500, 302):
            fetch.side_effect = HTTPError("http://auth.test", code, "private credentials", {}, None)
            with self.assertLogs(identity_module.LOG, level="WARNING") as logs:
                self.assertEqual(identity_module.IdentityNamesClient().names(["GV1"]), {"GV1": None})
            self.assertNotIn("private", str(logs.output))
            self.assertNotIn("service-secret", str(logs.output))

    @patch.object(identity_module.time, "monotonic", return_value=100)
    @patch.object(identity_module, "fetch_json", side_effect=TimeoutError())
    def test_circuit_opens_and_recovers(self, fetch, clock):
        for _ in range(4):
            self.assertEqual(self.client.names(["GV1"]), {"GV1": None})
        self.assertEqual(fetch.call_count, 3)
        clock.return_value = 111
        fetch.side_effect = None
        fetch.return_value = {"names": {"GV1": "Nguyen An"}}
        self.assertEqual(self.client.names(["GV1"]), {"GV1": "Nguyen An"})
        self.assertEqual(self.client.failures, 0)

    @patch.object(identity_module, "build_opener")
    def test_transport_post_body_limit_and_redirect_protection(self, opener):
        import json
        response = opener.return_value.open.return_value.__enter__.return_value
        response.read.return_value = b'{"names":{}}'
        self.assertEqual(identity_module.fetch_json("http://auth.test", {"X-Service-Token": "s"}, 2,
                                                   {"user_ids": []}), {"names": {}})
        sent = opener.return_value.open.call_args.args[0]
        self.assertEqual(sent.get_method(), "POST")
        self.assertEqual(json.loads(sent.data), {"user_ids": []})
        self.assertIsInstance(opener.call_args.args[0], identity_module.NoRedirect)
        self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 2)
        response.read.assert_called_with(262145)
        response.read.return_value = b"x" * 262145
        with self.assertRaises(ValueError):
            identity_module.fetch_json("http://auth.test", {}, 2)
        self.assertIsNone(identity_module.NoRedirect().redirect_request(None, None, 302, "", {}, "http://other"))
