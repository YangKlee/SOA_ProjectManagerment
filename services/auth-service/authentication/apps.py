from django.apps import AppConfig
from django.conf import settings
import os
import sys


class AuthenticationConfig(AppConfig):
    name = 'authentication'

    def ready(self):
        if not settings.CONSUL["AUTO_REGISTER"]:
            return

        # Django's development reloader starts a parent process first.  Only
        # the child process should create a Consul registration.
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        # Registration is deliberately skipped for administrative/test
        # commands, where no HTTP service is available for Consul to check.
        skipped_commands = {
            "check",
            "collectstatic",
            "makemigrations",
            "migrate",
            "register_consul",
            "shell",
            "test",
        }
        if any(command in sys.argv for command in skipped_commands):
            return

        from .consul import register_auth_service_in_background

        register_auth_service_in_background()
