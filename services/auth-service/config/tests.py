"""Verify settings initialization using isolated files and processes."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class EnvSettingsTests(SimpleTestCase):
    def load_settings(self, contents=None, overrides=None):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = root / "service"
            config = service / "config"
            config.mkdir(parents=True)
            target = config / "settings.py"
            shutil.copyfile(Path(__file__).with_name("settings.py"), target)
            if contents is not None:
                (service / ".env").write_text(contents, encoding="utf-8")
            # A cwd .env must never be used instead of the service's own file.
            (root / ".env").write_text('JWT_SIGNING_KEY="wrong-cwd-key"', encoding="utf-8")
            environment = {
                key: value for key, value in os.environ.items()
                if key not in {"JWT_SIGNING_KEY", "PYTHON_DOTENV_DISABLED"}
                and not key.startswith("CONSUL_")
            }
            environment.update(overrides or {})
            script = (
                "import json, runpy, sys; "
                "settings = runpy.run_path(sys.argv[1]); "
                "print(json.dumps({'key': settings['JWT_SIGNING_KEY'], "
                "'signing_key': settings['SIMPLE_JWT']['SIGNING_KEY'], "
                "'fallback': settings['JWT_SIGNING_KEY'] == settings['SECRET_KEY'], "
                "'consul': settings.get('CONSUL')}))"
            )
            result = subprocess.run(
                [sys.executable, "-c", script, str(target)], cwd=root,
                env=environment, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def test_service_file_loads_quoted_jwt_from_another_cwd(self):
        result = self.load_settings('# comment\nJWT_SIGNING_KEY="dummy-file-key"\n')
        self.assertEqual(result["key"], "dummy-file-key")
        self.assertEqual(result["signing_key"], "dummy-file-key")

    def test_process_environment_takes_precedence(self):
        result = self.load_settings(
            'JWT_SIGNING_KEY="dummy-file-key"\n',
            {"JWT_SIGNING_KEY": "dummy-process-key"},
        )
        self.assertEqual(result["key"], "dummy-process-key")
        self.assertEqual(result["signing_key"], "dummy-process-key")

    def test_missing_file_uses_existing_development_fallback(self):
        result = self.load_settings()
        self.assertTrue(result["fallback"])
        self.assertEqual(result["key"], result["signing_key"])

    def test_missing_file_still_accepts_environment(self):
        result = self.load_settings(overrides={"JWT_SIGNING_KEY": "dummy-process-key"})
        self.assertEqual(result["key"], "dummy-process-key")

    def test_consul_file_values_are_read_before_configuration(self):
        result = self.load_settings(
            'JWT_SIGNING_KEY="dummy-key"\n'
            'CONSUL_AUTO_REGISTER=true\n'
            'CONSUL_URL=http://registry.example.invalid:8500\n'
            'CONSUL_SERVICE_PORT=8123\n'
        )
        self.assertTrue(result["consul"]["AUTO_REGISTER"])
        self.assertEqual(result["consul"]["URL"], "http://registry.example.invalid:8500")
        self.assertEqual(result["consul"]["SERVICE_PORT"], "8123")

    def test_process_can_disable_consul_enabled_in_file(self):
        result = self.load_settings('CONSUL_AUTO_REGISTER=true\n', {"CONSUL_AUTO_REGISTER": "false"})
        self.assertFalse(result["consul"]["AUTO_REGISTER"])
