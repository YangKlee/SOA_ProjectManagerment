"""Environment contract regression: one internal credential, independent of JWT."""
import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.test import SimpleTestCase


class InternalTokenConfigurationTests(SimpleTestCase):
    def test_environment_token_is_loaded_and_empty_fails_closed(self):
        path = Path(__file__).with_name("settings.py")
        for token in ("unit-test-shared-credential", ""):
            with self.subTest(configured=bool(token)), patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": token}):
                config = runpy.run_path(str(path))
            self.assertEqual(config["INTERNAL_SERVICE_TOKEN"], token)

            self.assertEqual(config["IDENTITY_NAMES_CLIENT"]["SERVICE_TOKEN"], token)
            self.assertEqual(config["IDENTITY_MANAGEMENT_CLIENT"]["SERVICE_TOKEN"], token)
