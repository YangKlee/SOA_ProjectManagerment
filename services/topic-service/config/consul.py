"""Local registry plumbing; independent of other services' Python packages."""
import json
import logging
import os
import sys
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

LOG = logging.getLogger(__name__)


class RegistrationError(RuntimeError):
    pass


def register(deregister=False):
    config = settings.CONSUL
    instance_id = config["SERVICE_ID"]
    path = f"/v1/agent/service/deregister/{instance_id}" if deregister else "/v1/agent/service/register"
    payload = None if deregister else {
        "ID": instance_id, "Name": config["SERVICE_NAME"],
        "Address": config["SERVICE_ADDRESS"], "Port": int(config["SERVICE_PORT"]),
        "Check": {"HTTP": config["HEALTH_CHECK_URL"], "Interval": "10s",
                  "Timeout": "2s", "DeregisterCriticalServiceAfter": "1m"},
    }
    headers = {"Content-Type": "application/json"}
    if config.get("TOKEN"):
        headers["X-Consul-Token"] = config["TOKEN"]
    request = Request(config["URL"].rstrip("/") + path,
                      data=json.dumps(payload).encode() if payload else None,
                      headers=headers, method="PUT")
    try:
        with urlopen(request, timeout=float(config["TIMEOUT_SECONDS"])) as response:
            if not 200 <= response.status < 300:
                raise RegistrationError("Registry rejected service registration.")
    except (URLError, OSError) as exc:
        raise RegistrationError("Registry unavailable.") from exc


def registration_loop(stopping):
    delay = 1
    while not stopping.is_set():
        try:
            register()
            delay = 1
            if stopping.wait(30):
                return
        except RegistrationError:
            LOG.warning("Service registry unavailable; registration will retry")
            if stopping.wait(delay):
                return
            delay = min(delay * 2, 30)


def start_registration():
    if not settings.CONSUL["AUTO_REGISTER"]:
        return
    skipped = {"check", "test", "migrate", "makemigrations", "collectstatic",
               "shell", "register_consul", "createsuperuser", "showmigrations"}
    if skipped.intersection(sys.argv):
        return
    if "runserver" in sys.argv and "--noreload" not in sys.argv and os.getenv("RUN_MAIN") != "true":
        return
    threading.Thread(target=registration_loop, args=(threading.Event(),),
                     name="consul-registration", daemon=True).start()
