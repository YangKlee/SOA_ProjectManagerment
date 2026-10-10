"""Read-only academic name lookup, including identity enrichment through REST."""
from io import BytesIO

from django.db import OperationalError
from rest_framework import serializers
from rest_framework.exceptions import APIException, ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from MajorManager.models import Major
from .identity_client import identity_client
from .models import Lecturer


class BoundedJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        body = stream.read(65537)
        if len(body) > 65536:
            raise ParseError("Lookup body exceeds 64 KiB.")
        return super().parse(BytesIO(body), media_type, parser_context)


class TopicDisplayNamesRequestDTO(serializers.Serializer):
    major_ids = serializers.ListField(child=serializers.CharField(max_length=255), max_length=100)
    advisor_ids = serializers.ListField(child=serializers.CharField(max_length=255), max_length=100)

    def validate(self, attrs):
        if set(self.initial_data) != {"major_ids", "advisor_ids"}:
            raise serializers.ValidationError("Only major_ids and advisor_ids are accepted.")
        return {key: list(dict.fromkeys(value)) for key, value in attrs.items()}


class TopicDisplayNamesResponseDTO(serializers.Serializer):
    major_names = serializers.DictField(child=serializers.CharField(allow_null=True), read_only=True)
    advisor_names = serializers.DictField(child=serializers.CharField(allow_null=True), read_only=True)


class ReaderLookupThrottle(SimpleRateThrottle):
    rate = "120/min"
    scope = "academic-display-names"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": str(request.user.pk)}


class TopicDisplayNamesView(APIView):
    # POST carries a read-only batch: all authenticated readers are allowed.
    permission_classes = [IsAuthenticated]
    parser_classes = [BoundedJSONParser]
    throttle_classes = [ReaderLookupThrottle]

    def post(self, request):
        dto = TopicDisplayNamesRequestDTO(data=request.data)
        dto.is_valid(raise_exception=True)
        major_ids = dto.validated_data["major_ids"]
        advisor_ids = dto.validated_data["advisor_ids"]
        major_names = dict.fromkeys(major_ids)
        advisor_names = dict.fromkeys(advisor_ids)
        try:
            major_names.update(Major.objects.filter(pk__in=major_ids).values_list("major_id", "name"))
            existing_advisors = list(Lecturer.objects.filter(pk__in=advisor_ids).values_list("lecturer_id", flat=True))
        except OperationalError:
            error = APIException("Academic names are temporarily unavailable.")
            error.status_code = 503
            raise error from None
        if existing_advisors:
            advisor_names.update(identity_client.names(existing_advisors))
        return Response(TopicDisplayNamesResponseDTO({
            "major_names": major_names, "advisor_names": advisor_names,
        }).data)
