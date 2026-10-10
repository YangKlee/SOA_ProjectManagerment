"""Academic discovery is enabled by default; loopback is an explicit dev option."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class AcademicConfigurationTests(SimpleTestCase):
    def load_config(self, dotenv="", overrides=None):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = root / "topic-service"
            config = service / "config"
            config.mkdir(parents=True)
            settings = config / "settings.py"
            settings.write_text(Path(__file__).with_name("settings.py").read_text(encoding="utf-8"), encoding="utf-8")
            (service / ".env").write_text(dotenv, encoding="utf-8")
            # An unrelated caller directory must not determine service settings.
            (root / ".env").write_text(
                'ACADEMIC_DISCOVERY_ENABLED=false\nACADEMIC_BASE_URL=http://wrong-cwd.invalid:8002\n',
                encoding="utf-8",
            )
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith("ACADEMIC_") and key != "PYTHON_DOTENV_DISABLED"}
            environment.update(overrides or {})
            code = (
                "import json, runpy; "
                f"config = runpy.run_path({str(settings)!r}); "
                "print(json.dumps(config['ACADEMIC_CLIENT']))"
            )
            result = subprocess.run([sys.executable, "-B", "-c", code], cwd=root,
                                    env=environment, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)

    def test_discovery_stays_enabled_by_default(self):
        config = self.load_config()
        self.assertTrue(config["DISCOVERY_ENABLED"])
        self.assertEqual(config["TIMEOUT_SECONDS"], 2)

    def test_service_relative_dotenv_can_explicitly_enable_loopback_development(self):
        config = self.load_config(
            'ACADEMIC_DISCOVERY_ENABLED=false\nACADEMIC_BASE_URL=http://127.0.0.1:8002\n')
        self.assertFalse(config["DISCOVERY_ENABLED"])
        self.assertEqual(config["BASE_URL"], "http://127.0.0.1:8002")

    def test_process_environment_wins_over_service_dotenv(self):
        config = self.load_config(
            'ACADEMIC_DISCOVERY_ENABLED=false\nACADEMIC_BASE_URL=http://127.0.0.1:8002\n',
            {"ACADEMIC_DISCOVERY_ENABLED": "true", "ACADEMIC_BASE_URL": "http://academic.test:8002",
             "ACADEMIC_TIMEOUT_SECONDS": "1.5"},
        )
        self.assertTrue(config["DISCOVERY_ENABLED"])
        self.assertEqual(config["BASE_URL"], "http://academic.test:8002")
        self.assertEqual(config["TIMEOUT_SECONDS"], 1.5)
