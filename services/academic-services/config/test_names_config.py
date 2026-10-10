"""Local display-name transport is independent of identity-management transport."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class NamesConfigurationTests(SimpleTestCase):
    def load_config(self, contents="", overrides=None):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = root / "academic-service"
            directory = service / "config"
            directory.mkdir(parents=True)
            target = directory / "settings.py"
            target.write_text(Path(__file__).with_name("settings.py").read_text(encoding="utf-8"), encoding="utf-8")
            (service / ".env").write_text(contents, encoding="utf-8")
            (root / ".env").write_text(
                'AUTH_NAMES_DISCOVERY_ENABLED=false\nAUTH_NAMES_BASE_URL=http://wrong-cwd.invalid:8001\n',
                encoding="utf-8",
            )
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith(("AUTH_NAMES_", "AUTH_IDENTITY_"))
                           and key not in {"PYTHON_DOTENV_DISABLED", "INTERNAL_SERVICE_TOKEN"}}
            environment.update(overrides or {})
            code = (
                "import json,runpy; "
                f"settings=runpy.run_path({str(target)!r}); "
                "print(json.dumps({'names': settings['IDENTITY_NAMES_CLIENT'], "
                "'management': settings['IDENTITY_MANAGEMENT_CLIENT']}))"
            )
            result = subprocess.run([sys.executable, "-B", "-c", code], cwd=root, env=environment,
                                    capture_output=True, text=True, check=True, timeout=15)
            return json.loads(result.stdout)

    def test_defaults_keep_discovery_enabled_without_using_cwd_dotenv(self):
        config = self.load_config()
        self.assertTrue(config["names"]["DISCOVERY_ENABLED"])
        self.assertTrue(config["management"]["DISCOVERY_ENABLED"])
        self.assertEqual(config["names"]["BASE_URL"], "http://localhost:8001")

    def test_loopback_names_setting_does_not_change_identity_management(self):
        config = self.load_config(
            'AUTH_NAMES_DISCOVERY_ENABLED=false\nAUTH_NAMES_BASE_URL=http://127.0.0.1:8001\n'
            'INTERNAL_SERVICE_TOKEN=dummy-test-credential\n')
        self.assertFalse(config["names"]["DISCOVERY_ENABLED"])
        self.assertEqual(config["names"]["BASE_URL"], "http://127.0.0.1:8001")
        self.assertTrue(config["management"]["DISCOVERY_ENABLED"])
        self.assertEqual(config["names"]["SERVICE_TOKEN"], "dummy-test-credential")
        self.assertEqual(config["management"]["SERVICE_TOKEN"], "dummy-test-credential")

    def test_process_environment_overrides_service_names_dotenv(self):
        config = self.load_config(
            'AUTH_NAMES_DISCOVERY_ENABLED=false\nAUTH_NAMES_BASE_URL=http://127.0.0.1:8001\n',
            {"AUTH_NAMES_DISCOVERY_ENABLED": "true", "AUTH_NAMES_BASE_URL": "http://auth.test:8001",
             "INTERNAL_SERVICE_TOKEN": "dummy-process-credential"},
        )
        self.assertTrue(config["names"]["DISCOVERY_ENABLED"])
        self.assertEqual(config["names"]["BASE_URL"], "http://auth.test:8001")
        self.assertEqual(config["names"]["SERVICE_TOKEN"], "dummy-process-credential")
