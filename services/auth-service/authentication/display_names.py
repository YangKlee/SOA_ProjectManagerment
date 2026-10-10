"""Internal, display-name-only contract for academic-service."""
from hmac import compare_digest
from io import BytesIO

from django.conf import settings
from django.db import OperationalError
from rest_framework import serializers
from rest_framework.exceptions import APIException, ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .models import Users


class BoundedJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        body = stream.read(65537)
        if len(body) > 65536:
            raise ParseError("Lookup body exceeds 64 KiB.")
        return super().parse(BytesIO(body), media_type, parser_context)


class DisplayNamesRequestDTO(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.CharField(max_length=255), max_length=100)

    def validate(self, attrs):
        if set(self.initial_data) != {"user_ids"}:
            raise serializers.ValidationError("Only user_ids is accepted.")
        attrs["user_ids"] = list(dict.fromkeys(attrs["user_ids"]))
        return attrs


class DisplayNamesResponseDTO(serializers.Serializer):
    names = serializers.DictField(child=serializers.CharField(allow_null=True), read_only=True)


class AcademicServicePermission(BasePermission):
    message = "Service credentials required."

    def has_permission(self, request, view):
        expected = settings.DISPLAY_NAMES_SERVICE_TOKEN
        supplied = request.headers.get("X-Service-Token", "")
        return bool(expected and supplied and compare_digest(expected.encode(), supplied.encode()))


class ServiceLookupThrottle(SimpleRateThrottle):
    rate = "120/min"
    scope = "internal-display-names"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": "academic-service"}


class UserDisplayNamesView(APIView):
    authentication_classes = []
    permission_classes = [AcademicServicePermission]
    parser_classes = [BoundedJSONParser]
    throttle_classes = [ServiceLookupThrottle]

    def post(self, request):
        dto = DisplayNamesRequestDTO(data=request.data)
        dto.is_valid(raise_exception=True)
        ids = dto.validated_data["user_ids"]
        names = dict.fromkeys(ids)
        try:
            rows = Users.objects.filter(userid__in=ids).values_list("userid", "lastname", "firstname")
            for user_id, last_name, first_name in rows:
                names[user_id] = " ".join(part.strip() for part in (last_name or "", first_name or "") if part.strip()) or None
        except OperationalError:
            error = APIException("Identity names are temporarily unavailable.")
            error.status_code = 503
            raise error from None
        return Response(DisplayNamesResponseDTO({"names": names}).data)
