import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from .consul import ConsulClient, ConsulServiceSettings


class ConsulClientTests(SimpleTestCase):
    def setUp(self):
        self.config = ConsulServiceSettings(
            base_url="http://localhost:8500",
            service_name="auth-service",
            instance_id="auth-service-8001",
            address="host.docker.internal",
            port=8001,
            health_check_url="http://host.docker.internal:8001/health/",
            token="test-token",
            timeout_seconds=3,
        )

    @patch("authentication.consul.urlopen")
    def test_register_sends_consul_service_definition(self, mocked_urlopen):
        response = MagicMock(status=200)
        mocked_urlopen.return_value.__enter__.return_value = response

        ConsulClient(self.config).register()

        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "http://localhost:8500/v1/agent/service/register")
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(request.get_header("X-consul-token"), "test-token")
        self.assertEqual(payload["Name"], "auth-service")
        self.assertEqual(payload["Port"], 8001)
        self.assertEqual(payload["Check"]["HTTP"], "http://host.docker.internal:8001/health/")

    @patch("authentication.consul.urlopen")
    def test_deregister_uses_service_instance_id(self, mocked_urlopen):
        response = MagicMock(status=200)
        mocked_urlopen.return_value.__enter__.return_value = response

        ConsulClient(self.config).deregister()

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://localhost:8500/v1/agent/service/deregister/auth-service-8001",
        )
        self.assertEqual(request.get_method(), "PUT")
