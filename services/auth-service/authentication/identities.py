"""Auth-owned identity lifecycle. Never mount this contract at the public gateway."""
from hmac import compare_digest
import logging
import re
from uuid import uuid4

from django.conf import settings
from django.db import DatabaseError, IntegrityError, transaction
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, MethodNotAllowed
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .display_names import BoundedJSONParser, ServiceLookupThrottle
from .models import Users
from .serializers import UserResponseSerializer

ROLES = {"students": 3, "lecturers": 2}
LOG = logging.getLogger(__name__)


class IdentityInput(serializers.Serializer):
    user_id = serializers.RegexField(r"^(?!\.{1,2}$)[^/\\\x00-\x1f\x7f]+$", max_length=255, required=False)
    last_name = serializers.CharField(max_length=255, allow_null=True, allow_blank=True, required=False)
    first_name = serializers.CharField(max_length=255, allow_null=True, allow_blank=True, required=False)
    gender = serializers.IntegerField(allow_null=True, required=False, min_value=-(2**63), max_value=2**63-1)
    date_of_birth = serializers.DateField(allow_null=True, required=False)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=50)
    status = serializers.IntegerField(allow_null=True, required=False, min_value=-(2**63), max_value=2**63-1)
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "Unknown or read-only field." for key in unknown})
        return attrs


class IdentityServiceAdmin(BasePermission):
    def has_permission(self, request, view):
        expected = settings.INTERNAL_SERVICE_TOKEN
        supplied = request.headers.get("X-Service-Token", "")
        return bool(expected and supplied and compare_digest(expected.encode(), supplied.encode())
                    and request.user.is_authenticated and request.user.role == 1
                    and request.auth and request.auth.get("role") == 1)


class IdentityThrottle(ServiceLookupThrottle):
    scope = "internal-identity-management"


def conflict(detail):
    error = APIException(detail)
    error.status_code = 409
    raise error


def values(data):
    mapping = {"user_id": "userid", "last_name": "lastname", "first_name": "firstname",
               "date_of_birth": "dateofbirth"}
    return {mapping.get(key, key): value.isoformat() if key == "date_of_birth" and value else value
            for key, value in data.items()}


class IdentityView(APIView):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IdentityServiceAdmin]
    parser_classes = [BoundedJSONParser]
    throttle_classes = [IdentityThrottle]

    def finalize_response(self, request, response, *args, **kwargs):
        correlation = request.headers.get("X-Request-ID", "")
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", correlation):
            correlation = str(uuid4())
        response["X-Request-ID"] = correlation
        LOG.info("Identity management method=%s kind=%s status=%s request_id=%s",
                 request.method, kwargs.get("kind", "unknown"), response.status_code, correlation)
        return super().finalize_response(request, response, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if type(self) is IdentityView and request.method not in {"OPTIONS"}:
            detail = "user_id" in kwargs
            if (request.method == "POST" and detail) or (request.method in {"GET", "HEAD", "PATCH", "DELETE"} and not detail):
                raise MethodNotAllowed(request.method)

    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            exc = APIException("Identity conflicts with an existing account or is referenced by other records.")
            exc.status_code = 409
        elif isinstance(exc, DatabaseError):
            exc = APIException("Identity database is temporarily unavailable.")
            exc.status_code = 503
        return super().handle_exception(exc)

    def role(self, kind):
        if kind not in ROLES:
            raise NotFound()
        return ROLES[kind]

    def target(self, request, kind, user_id):
        role = self.role(kind)
        try:
            user = Users.objects.get(userid=user_id)
        except Users.DoesNotExist:
            raise NotFound("Identity does not exist.") from None
        if user.role != role or user.userid == request.user.userid:
            raise PermissionDenied("Identity does not belong to this capability.")
        return user

    def get(self, request, kind, user_id):
        return Response(UserResponseSerializer(self.target(request, kind, user_id)).data)

    def post(self, request, kind):
        role = self.role(kind)
        dto = IdentityInput(data=request.data)
        dto.is_valid(raise_exception=True)
        if not dto.validated_data.get("user_id"):
            raise serializers.ValidationError({"user_id": "This field is required."})
        data = values(dto.validated_data)
        stamp = now().isoformat()
        # The unique constraints are the final authority, including concurrent requests.
        with transaction.atomic():
            user = Users.objects.create(**data, role=role, createdat=stamp, updatedat=stamp)
        return Response(UserResponseSerializer(user).data, status=201)

    def patch(self, request, kind, user_id):
        dto = IdentityInput(data=request.data, partial=True)
        dto.is_valid(raise_exception=True)
        if "user_id" in dto.validated_data:
            raise serializers.ValidationError({"user_id": "User ID is immutable."})
        with transaction.atomic():
            user = self.target(request, kind, user_id)
            data = values(dto.validated_data)
            for key, value in data.items():
                setattr(user, key, value)
            user.updatedat = now().isoformat()
            user.save(update_fields=[*data, "updatedat"])
        return Response(UserResponseSerializer(user).data)

    def delete(self, request, kind, user_id):
        with transaction.atomic():
            self.target(request, kind, user_id).delete()
        return Response(status=204)


class IdentityBatchInput(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.CharField(max_length=255), max_length=100)

    def validate(self, attrs):
        if set(self.initial_data) != {"user_ids"}:
            raise serializers.ValidationError("Only user_ids is accepted.")
        return attrs


class IdentityBatchView(IdentityView):
    http_method_names = ["post", "options"]
    def post(self, request, kind):
        role = self.role(kind)
        dto = IdentityBatchInput(data=request.data)
        dto.is_valid(raise_exception=True)
        profiles = dict.fromkeys(dto.validated_data["user_ids"])
        for user in Users.objects.filter(userid__in=profiles, role=role):
            profiles[user.userid] = UserResponseSerializer(user).data
        return Response({"users": profiles})
