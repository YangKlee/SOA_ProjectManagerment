"""Local auth-service contract client. Never import auth ORM or expose its token."""
import ipaddress
import json
import logging
import re
import threading
import time
from http.client import HTTPException
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings

LOG = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_json(url, headers, timeout, data=None):
    headers = {"Accept": "application/json", **headers}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, headers=headers, data=json.dumps(data).encode() if data is not None else None)
    with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        body = response.read(262145)
        if len(body) > 262144:
            raise ValueError("Oversized response")
        return json.loads(body)


def instance_url(address, port):
    if not isinstance(address, str) or not address or len(address) > 253:
        raise ValueError("Invalid address")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Invalid port")
    try:
        ip = ipaddress.ip_address(address)
        address = f"[{ip}]" if ip.version == 6 else str(ip)
    except ValueError:
        if not all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part)
                   for part in address.split(".")):
            raise ValueError("Invalid hostname") from None
    return f"http://{address}:{port}"


class IdentityNamesClient:
    def __init__(self):
        self.failures = 0
        self.open_until = 0
        self.lock = threading.Lock()

    def base_url(self, config):
        if not config["DISCOVERY_ENABLED"]:
            base = config["BASE_URL"].rstrip("/")
            parsed = urlsplit(base)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
                raise ValueError("Invalid development URL")
            return base
        consul = settings.CONSUL
        headers = {"X-Consul-Token": consul["TOKEN"]} if consul.get("TOKEN") else {}
        instances = fetch_json(consul["URL"].rstrip("/") + "/v1/health/service/auth-service?passing=true",
                               headers, config["TIMEOUT_SECONDS"])
        if not isinstance(instances, list) or not instances:
            raise ValueError("No healthy auth instance")
        for item in instances:
            service = item["Service"]
            checks = item["Checks"]
            if service["Service"] != "auth-service" or not isinstance(checks, list) or not checks:
                raise ValueError("Invalid registry response")
            if all(check["Status"] == "passing" for check in checks):
                return instance_url(service.get("Address") or item["Node"]["Address"], service["Port"])
        raise ValueError("No healthy auth instance")

    def names(self, user_ids):
        ids = list(dict.fromkeys(user_ids))
        fallback = dict.fromkeys(ids)
        if not ids:
            return fallback
        config = settings.IDENTITY_NAMES_CLIENT
        with self.lock:
            if time.monotonic() < self.open_until:
                return fallback
        try:
            if not config["SERVICE_TOKEN"] or len(ids) > 100:
                raise ValueError("Unconfigured or oversized lookup")
            base = self.base_url(config)
            payload = fetch_json(base + "/internal/v1/user-display-names/",
                                 {"X-Service-Token": config["SERVICE_TOKEN"]}, config["TIMEOUT_SECONDS"],
                                 {"user_ids": ids})
            names = payload["names"]
            if not isinstance(names, dict) or set(names) != set(ids) or any(
                    value is not None and not isinstance(value, str) for value in names.values()):
                raise ValueError("Invalid display-name DTO")
        except (OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError):
            with self.lock:
                self.failures += 1
                if self.failures >= 3:
                    self.open_until = time.monotonic() + 10
            LOG.warning("Identity display-name lookup unavailable")
            return fallback
        with self.lock:
            self.failures = 0
            self.open_until = 0
        return names


identity_client = IdentityNamesClient()
