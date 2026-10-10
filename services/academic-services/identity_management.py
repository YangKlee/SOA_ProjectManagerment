"""Versioned identity contract client; only auth-service touches Users."""
import json
import re
import time
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, build_opener

from django.conf import settings
from rest_framework.exceptions import APIException

from LectureManager.identity_client import IdentityNamesClient, NoRedirect


class IdentityFailure(APIException):
    status_code = 503

    def __init__(self, detail="Identity service unavailable.", status=503, uncertain=False):
        self.status_code = status
        self.uncertain = uncertain
        super().__init__(detail)


PROFILE_FIELDS = {"user_id", "first_name", "last_name", "gender", "date_of_birth", "email",
                  "phone", "role", "status", "created_at", "updated_at"}


def correlation_id(request):
    value = getattr(request, "identity_request_id", request.headers.get("X-Request-ID", ""))
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", value):
        from uuid import uuid4
        value = str(uuid4())
    request.identity_request_id = value
    return value


def safe_profile(value, user_id, kind):
    if not isinstance(value, dict) or set(value) != PROFILE_FIELDS or value.get("user_id") != user_id:
        raise ValueError("Invalid identity DTO")
    if value.get("role") != {"students": 3, "lecturers": 2}[kind]:
        raise ValueError("Mismatched identity role")
    for key in PROFILE_FIELDS - {"gender", "status", "role"}:
        if value[key] is not None and (not isinstance(value[key], str) or len(value[key]) > 1024):
            raise ValueError("Invalid identity field")
    for key in ("gender", "status"):
        if value[key] is not None and type(value[key]) is not int:
            raise ValueError("Invalid integer")
    if not value["email"] or not value["phone"]:
        raise ValueError("Missing identity field")
    return value


class IdentityClient(IdentityNamesClient):
    def call(self, request, kind, method="GET", user_id=None, data=None, batch=False):
        config = settings.IDENTITY_MANAGEMENT_CLIENT
        writing = method in {"POST", "PATCH", "DELETE"} and not batch
        sent = False
        correlation = correlation_id(request)
        with self.lock:
            if time.monotonic() < self.open_until:
                raise IdentityFailure()
        try:
            if not config["SERVICE_TOKEN"]:
                raise ValueError("Missing identity service credential")
            base = self.base_url(config)
            path = f"/internal/v1/identity-profiles/{kind}/" if batch else f"/internal/v1/identities/{kind}/"
            if user_id is not None:
                path += quote(user_id, safe="") + "/"
            headers = {"Accept": "application/json", "Content-Type": "application/json",
                       "X-Service-Token": config["SERVICE_TOKEN"], "X-Request-ID": correlation,
                       "Authorization": request.headers.get("Authorization", "")}
            req = Request(base + path, method=method, headers=headers,
                          data=json.dumps(data).encode() if data is not None else None)
            sent = True
            with build_opener(NoRedirect()).open(req, timeout=config["TIMEOUT_SECONDS"]) as response:
                expected = 204 if method == "DELETE" else 201 if method == "POST" and not batch else 200
                if response.status != expected:
                    raise ValueError("Unexpected identity response status")
                body = response.read(262145)
                if len(body) > 262144:
                    raise ValueError("Oversized identity response")
                result = None if method == "DELETE" else json.loads(body)
                if batch:
                    users = result["users"]
                    if not isinstance(users, dict) or set(users) != set(data["user_ids"]):
                        raise ValueError("Invalid batch")
                    result = {key: safe_profile(value, key, kind) if value is not None else None
                              for key, value in users.items()}
                elif method != "DELETE":
                    result = safe_profile(result, user_id or data["user_id"], kind)
        except HTTPError as exc:
            # Only contract-defined 4xx are confirmed rejections; redirects/5xx are uncertain writes.
            if exc.code in {400, 401, 403, 404, 409, 429}:
                messages = {400: "Invalid identity fields.", 401: "Identity authorization failed.",
                            403: "Identity authorization failed or role mismatch.", 404: "Identity does not exist.",
                            409: "Email, phone or ID already exists, or identity is referenced.",
                            429: "Identity service rate limit reached."}
                status = exc.code if exc.code in {400, 404, 409} else 503
                raise IdentityFailure(messages[exc.code], status=status) from None
            self.failed()
            raise IdentityFailure(uncertain=writing and sent) from None
        except (OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError):
            self.failed()
            raise IdentityFailure(uncertain=writing and sent) from None
        with self.lock:
            self.failures = 0
            self.open_until = 0
        return result

    def failed(self):
        with self.lock:
            self.failures += 1
            if self.failures >= 3:
                self.open_until = time.monotonic() + 10


identity_management = IdentityClient()
