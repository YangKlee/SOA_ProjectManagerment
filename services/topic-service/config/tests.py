

from io import StringIO
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from config import consul


class RegistryTests(SimpleTestCase):
    def setUp(self):
        self.config = dict(settings.CONSUL, AUTO_REGISTER=True, TOKEN="dummy-token")
        self.override = override_settings(CONSUL=self.config)
        self.override.enable()
        self.addCleanup(self.override.disable)

    @patch("config.consul.urlopen")
    def test_registration_contract_and_timeout(self, request):
        import json
        request.return_value.__enter__.return_value.status = 200
        consul.register()
        sent = request.call_args.args[0]
        payload = json.loads(sent.data)
        self.assertEqual(sent.get_method(), "PUT")
        self.assertTrue(sent.full_url.endswith("/v1/agent/service/register"))
        self.assertEqual(sent.get_header("X-consul-token"), "dummy-token")
        self.assertEqual(payload["Name"], self.config["SERVICE_NAME"])
        self.assertEqual(payload["Port"], int(self.config["SERVICE_PORT"]))
        self.assertEqual(payload["Check"]["HTTP"], self.config["HEALTH_CHECK_URL"])
        self.assertEqual(payload["Check"]["DeregisterCriticalServiceAfter"], "1m")
        self.assertEqual(request.call_args.kwargs["timeout"], 3)

    @patch("config.consul.urlopen")
    def test_deregister_command(self, request):
        request.return_value.__enter__.return_value.status = 200
        call_command("register_consul", deregister=True, stdout=StringIO())
        self.assertTrue(request.call_args.args[0].full_url.endswith(
            "/v1/agent/service/deregister/" + self.config["SERVICE_ID"]))

    @patch("config.consul.urlopen", side_effect=URLError("private connection detail"))
    def test_connection_failure_has_safe_error(self, request):
        with self.assertRaises(consul.RegistrationError) as caught:
            consul.register()
        self.assertNotIn("private", str(caught.exception))

    @patch("config.consul.register", side_effect=[consul.RegistrationError(), consul.RegistrationError(), None])
    def test_retry_backoff_recovers(self, register):
        stopping = MagicMock()
        stopping.is_set.return_value = False
        stopping.wait.side_effect = [False, False, True]
        consul.registration_loop(stopping)
        self.assertEqual([call.args[0] for call in stopping.wait.call_args_list], [1, 2, 30])

    @patch("config.consul.register", side_effect=consul.RegistrationError())
    def test_retry_backoff_is_bounded(self, register):
        stopping = MagicMock()
        stopping.is_set.return_value = False
        stopping.wait.side_effect = [False] * 8 + [True]
        consul.registration_loop(stopping)
        self.assertEqual(max(call.args[0] for call in stopping.wait.call_args_list), 30)

    @patch("config.consul.threading.Thread")
    def test_admin_commands_and_reloader_parent_do_not_register(self, thread):
        for command in ["test", "check", "migrate", "register_consul"]:
            with patch("config.consul.sys.argv", ["manage.py", command]):
                consul.start_registration()
        with patch("config.consul.sys.argv", ["manage.py", "runserver"]), \
             patch.dict("os.environ", {"RUN_MAIN": "false"}):
            consul.start_registration()
        thread.assert_not_called()

    @patch("config.consul.threading.Thread")
    def test_server_starts_daemon_without_blocking(self, thread):
        with patch("config.consul.sys.argv", ["manage.py", "runserver", "--noreload"]):
            consul.start_registration()
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs["daemon"])
        thread.return_value.start.assert_called_once_with()

    def test_health_is_public_and_container_host_allowed(self):
        response = self.client.get("/health/", HTTP_HOST="host.docker.internal")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], self.config["SERVICE_NAME"])
        self.assertEqual(self.client.get("/health/", HTTP_HOST="untrusted.invalid").status_code, 400)


class RegistryEnvironmentTests(SimpleTestCase):
    def test_local_file_loading_and_process_precedence(self):
        import os
        from pathlib import Path
        import runpy
        import shutil
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.mkdir()
            target = config / "settings.py"
            shutil.copyfile(Path(__file__).with_name("settings.py"), target)
            (Path(directory) / ".env").write_text(
                'CONSUL_SERVICE_ID="file-instance"\nCONSUL_AUTO_REGISTER=true\n'
                'ALLOWED_HOSTS=allowed.example.invalid\n', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                loaded = runpy.run_path(str(target))
                self.assertEqual(loaded["CONSUL"]["SERVICE_ID"], "file-instance")
                self.assertTrue(loaded["CONSUL"]["AUTO_REGISTER"])
                self.assertEqual(loaded["ALLOWED_HOSTS"], ["allowed.example.invalid"])
            with patch.dict(os.environ, {"CONSUL_SERVICE_ID": "process-instance",
                                         "CONSUL_AUTO_REGISTER": "false"}, clear=True):
                loaded = runpy.run_path(str(target))
                self.assertEqual(loaded["CONSUL"]["SERVICE_ID"], "process-instance")
                self.assertFalse(loaded["CONSUL"]["AUTO_REGISTER"])
