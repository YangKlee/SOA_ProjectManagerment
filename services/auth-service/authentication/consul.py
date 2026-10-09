"""Small Consul client used to register this service through Consul's HTTP API."""

import json
import logging
import threading
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)


class ConsulRegistrationError(RuntimeError):
    """Raised when Consul cannot accept a registration request."""


@dataclass(frozen=True)
class ConsulServiceSettings:
    base_url: str
    service_name: str
    instance_id: str
    address: str
    port: int
    health_check_url: str
    token: str | None
    timeout_seconds: int

    @classmethod
    def from_django_settings(cls):
        config = settings.CONSUL
        return cls(
            base_url=config["URL"].rstrip("/"),
            service_name=config["SERVICE_NAME"],
            instance_id=config["SERVICE_ID"],
            address=config["SERVICE_ADDRESS"],
            port=int(config["SERVICE_PORT"]),
            health_check_url=config["HEALTH_CHECK_URL"],
            token=config.get("TOKEN") or None,
            timeout_seconds=int(config["TIMEOUT_SECONDS"]),
        )


class ConsulClient:
    def __init__(self, config: ConsulServiceSettings):
        self.config = config

    def register(self):
        payload = {
            "ID": self.config.instance_id,
            "Name": self.config.service_name,
            "Address": self.config.address,
            "Port": self.config.port,
            "Check": {
                "HTTP": self.config.health_check_url,
                "Interval": "10s",
                "Timeout": "2s",
                "DeregisterCriticalServiceAfter": "1m",
            },
        }
        self._request("PUT", "/v1/agent/service/register", payload)

    def deregister(self):
        self._request(
            "PUT", f"/v1/agent/service/deregister/{self.config.instance_id}", None
        )

    def _request(self, method, path, payload):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.config.token:
            headers["X-Consul-Token"] = self.config.token

        request = Request(
            f"{self.config.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                if not 200 <= response.status < 300:
                    raise ConsulRegistrationError(
                        f"Consul returned HTTP {response.status} for {path}."
                    )
        except URLError as exc:
            raise ConsulRegistrationError(
                f"Could not connect to Consul at {self.config.base_url}."
            ) from exc


def register_auth_service():
    """Register the configured auth-service instance with Consul."""
    config = ConsulServiceSettings.from_django_settings()
    ConsulClient(config).register()
    logger.info("Registered %s with Consul.", config.instance_id)


def deregister_auth_service():
    config = ConsulServiceSettings.from_django_settings()
    ConsulClient(config).deregister()
    logger.info("Deregistered %s from Consul.", config.instance_id)


def register_auth_service_in_background():
    """Do not make an unavailable registry prevent Django from starting."""

    def register():
        try:
            register_auth_service()
        except ConsulRegistrationError:
            logger.warning("Auth service could not register with Consul.", exc_info=True)

    threading.Thread(target=register, name="consul-registration", daemon=True).start()
