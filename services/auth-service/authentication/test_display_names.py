from unittest.mock import patch

from django.core.cache import cache
from django.db import OperationalError
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .display_names import ServiceLookupThrottle
from .models import Users


@override_settings(DISPLAY_NAMES_SERVICE_TOKEN="test-service-secret")
class UserDisplayNamesTests(SimpleTestCase):
    url = "/internal/v1/user-display-names/"

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.client.credentials(HTTP_X_SERVICE_TOKEN="test-service-secret")

    def post(self, data):
        return self.client.post(self.url, data, format="json")

    @patch.object(Users.objects, "filter")
    def test_display_only_names_and_missing_rows(self, users):
        users.return_value.values_list.return_value = [
            ("GV1", " Nguyen ", " An "), ("GV2", None, "Binh"), ("GV3", None, None)]
        response = self.post({"user_ids": ["GV1", "GV2", "GV3", "missing", "GV1"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"names": {"GV1": "Nguyen An", "GV2": "Binh", "GV3": None, "missing": None}})
        users.assert_called_once_with(userid__in=["GV1", "GV2", "GV3", "missing"])
        users.return_value.values_list.assert_called_once_with("userid", "lastname", "firstname")
        self.assertNotIn("password", str(response.data))
        self.assertNotIn("email", str(response.data))

    @patch.object(Users.objects, "filter")
    def test_service_auth_is_required_and_fails_closed(self, users):
        token = AccessToken()
        token["user_id"] = "admin"
        token["role"] = 1
        for credentials in ({}, {"HTTP_X_SERVICE_TOKEN": "wrong"}, {"HTTP_AUTHORIZATION": f"Bearer {token}"}):
            self.client.credentials(**credentials)
            self.assertEqual(self.post({"user_ids": ["GV1"]}).status_code, 403)
        self.client.credentials(HTTP_X_SERVICE_TOKEN="test-service-secret")
        with override_settings(DISPLAY_NAMES_SERVICE_TOKEN=""):
            self.assertEqual(self.post({"user_ids": ["GV1"]}).status_code, 403)
        users.assert_not_called()

    @patch.object(Users.objects, "filter")
    def test_bounded_input_and_unknown_fields(self, users):
        for payload in ({}, {"user_ids": [""]}, {"user_ids": ["x" * 256]},
                        {"user_ids": ["x"] * 101}, {"user_ids": [], "email": True},
                        {"user_ids": ["x" * 65537]}):
            self.assertEqual(self.post(payload).status_code, 400)
        users.assert_not_called()

    @patch.object(Users.objects, "filter", side_effect=OperationalError("private schema"))
    def test_storage_error_is_safe(self, users):
        response = self.post({"user_ids": ["GV1"]})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", str(response.data))

    @patch.object(Users.objects, "filter")
    def test_process_cache_rate_limit(self, users):
        users.return_value.values_list.return_value = []
        with patch.object(ServiceLookupThrottle, "rate", "1/min"):
            self.assertEqual(self.post({"user_ids": []}).status_code, 200)
            self.assertEqual(self.post({"user_ids": []}).status_code, 429)
