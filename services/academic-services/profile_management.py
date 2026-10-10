"""Composite academic capabilities, with explicit compensation across HTTP boundaries.

There is intentionally no SQLite write transaction spanning an identity HTTP call.
An uncertain write is never replayed or reported as successful.
"""
import math
import logging

from django.db import DatabaseError, IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, MethodNotAllowed
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from LectureManager.models import Lecturer
from LectureManager.services import _validate_department
from StudentManager.models import Student
from StudentManager.services import _validate
from identity_management import IdentityFailure, identity_management, correlation_id
from LectureManager.display_names import BoundedJSONParser

LOG = logging.getLogger(__name__)


class ProfileInput(serializers.Serializer):
    last_name = serializers.CharField(max_length=255, allow_null=True, allow_blank=True, required=False)
    first_name = serializers.CharField(max_length=255, allow_null=True, allow_blank=True, required=False)
    gender = serializers.IntegerField(allow_null=True, required=False, min_value=-(2**63), max_value=2**63-1)
    date_of_birth = serializers.DateField(allow_null=True, required=False)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=50)
    status = serializers.IntegerField(allow_null=True, required=False, min_value=-(2**63), max_value=2**63-1)
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)

    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - set(self.fields):
            raise serializers.ValidationError("Unknown or read-only identity fields.")
        return super().to_internal_value(data)

    def validate(self, attrs):
        if "date_of_birth" in attrs and attrs["date_of_birth"]:
            attrs["date_of_birth"] = attrs["date_of_birth"].isoformat()
        return attrs


class CompositeInput(serializers.Serializer):
    user = ProfileInput()

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Unknown or read-only academic fields.")
        if "gpa" in attrs and not math.isfinite(attrs["gpa"]):
            raise serializers.ValidationError({"gpa": "Must be finite."})
        return attrs


class StudentInput(CompositeInput):
    student_id = serializers.RegexField(r"^(?!\.{1,2}$)[^/\\\x00-\x1f\x7f]+$", max_length=255)
    major_id = serializers.CharField(max_length=255)
    sub_major_id = serializers.CharField(max_length=255, allow_null=True, required=False)
    accumulated_credits = serializers.IntegerField(min_value=-(2**63), max_value=2**63-1)
    gpa = serializers.FloatField()


class LecturerInput(CompositeInput):
    lecturer_id = serializers.RegexField(r"^(?!\.{1,2}$)[^/\\\x00-\x1f\x7f]+$", max_length=255)
    department_id = serializers.CharField(max_length=255, allow_null=True, required=False)


class ProfileOutput(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True, allow_null=True)
    first_name = serializers.CharField(read_only=True, allow_null=True)
    gender = serializers.IntegerField(read_only=True, allow_null=True)
    date_of_birth = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    status = serializers.IntegerField(read_only=True, allow_null=True)
    role = serializers.IntegerField(read_only=True)
    created_at = serializers.CharField(read_only=True, allow_null=True)
    updated_at = serializers.CharField(read_only=True, allow_null=True)


class StudentOutput(serializers.Serializer):
    student_id = serializers.CharField(read_only=True)
    major_id = serializers.CharField(read_only=True)
    sub_major_id = serializers.CharField(read_only=True, allow_null=True)
    accumulated_credits = serializers.IntegerField(read_only=True)
    gpa = serializers.FloatField(read_only=True)
    user = ProfileOutput(read_only=True, allow_null=True)


class LecturerOutput(serializers.Serializer):
    lecturer_id = serializers.CharField(read_only=True)
    department_id = serializers.CharField(read_only=True, allow_null=True)
    user = ProfileOutput(read_only=True, allow_null=True)


class Administrator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.auth and request.auth.get("role") == 1)


def incomplete():
    error = APIException({"code": "operation_incomplete", "detail":
        "Operation outcome is uncertain. Reload and reconcile academic/identity records before retrying."})
    error.status_code = 503
    raise error


def conflict(message):
    error = APIException(message)
    error.status_code = 409
    raise error


class CompositeView(APIView):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [Administrator]
    parser_classes = [BoundedJSONParser]
    kind = None

    def output(self, data, many=False):
        return (StudentOutput if self.kind == "students" else LecturerOutput)(data, many=many).data

    def finalize_response(self, request, response, *args, **kwargs):
        correlation = correlation_id(request)
        response["X-Request-ID"] = correlation
        LOG.info("Academic profile management method=%s kind=%s status=%s request_id=%s",
                 request.method, self.kind, response.status_code, correlation)
        return super().finalize_response(request, response, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        correlation_id(request)
        super().initial(request, *args, **kwargs)
        detail = "pk" in kwargs
        if (request.method == "POST" and detail) or (request.method in {"PATCH", "DELETE"} and not detail):
            raise MethodNotAllowed(request.method)

    @property
    def model(self):
        return Student if self.kind == "students" else Lecturer

    @property
    def fields(self):
        return ["student_id", "major_id", "sub_major_id", "accumulated_credits", "gpa"] if self.kind == "students" else ["lecturer_id", "department_id"]

    def snapshot(self, row):
        return {field: getattr(row, field) for field in self.fields}

    def get_row(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            raise NotFound("Academic record does not exist.") from None

    def validate_academic(self, data):
        try:
            if self.kind == "students":
                _validate(data)
            else:
                _validate_department(data)
        except ValueError as exc:
            raise serializers.ValidationError(exc.errors) from None

    def identity(self, request, method="GET", pk=None, data=None, batch=False):
        return identity_management.call(request, self.kind, method, pk, data, batch)

    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            exc = APIException("Academic record conflicts with existing or referenced data.")
            exc.status_code = 409
        elif isinstance(exc, DatabaseError):
            exc = APIException("Academic database is temporarily unavailable.")
            exc.status_code = 503
        return super().handle_exception(exc)

    def get(self, request, pk=None):
        if pk is not None:
            row = self.snapshot(self.get_row(pk))
            return Response(self.output({**row, "user": self.identity(request, pk=pk)}))
        rows = [self.snapshot(row) for row in self.model.objects.all()]
        profiles = {}
        ids = [row[self.fields[0]] for row in rows]
        for offset in range(0, len(ids), 100):
            profiles.update(self.identity(request, "POST", data={"user_ids": ids[offset:offset + 100]}, batch=True))
        return Response(self.output([{**row, "user": profiles[row[self.fields[0]]]} for row in rows], many=True))

    def input(self, request, partial=False):
        dto = (StudentInput if self.kind == "students" else LecturerInput)(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        data = dict(dto.validated_data)
        return data, data.pop("user", {})

    def post(self, request):
        data, user = self.input(request)
        self.validate_academic(data)
        pk = data[self.fields[0]]
        if self.model.objects.filter(pk=pk).exists():
            conflict("Academic ID already exists.")
        try:
            profile = self.identity(request, "POST", data={**user, "user_id": pk})
        except IdentityFailure as exc:
            if exc.uncertain:
                incomplete()
            raise
        try:
            with transaction.atomic():
                row = self.model.objects.create(**data)
        except DatabaseError:
            try:
                self.identity(request, "DELETE", pk=pk)
            except IdentityFailure:
                incomplete()
            raise
        return Response(self.output({**self.snapshot(row), "user": profile}), status=201)

    def patch(self, request, pk):
        data, user = self.input(request, partial=True)
        if self.fields[0] in data:
            if data.pop(self.fields[0]) != pk:
                raise serializers.ValidationError({self.fields[0]: "ID is immutable."})
        before = self.snapshot(self.get_row(pk))
        after = {**before, **data}
        self.validate_academic(after)
        profile = self.identity(request, pk=pk)  # Validate role/ownership before local writes.
        with transaction.atomic():
            if self.model.objects.filter(**before).update(**data) != 1 and data:
                conflict("Academic record changed. Reload before editing.")
        try:
            if user:
                profile = self.identity(request, "PATCH", pk=pk, data=user)
        except IdentityFailure as exc:
            if exc.uncertain:
                incomplete()
            try:
                with transaction.atomic():
                    if self.model.objects.filter(**after).update(**{k: before[k] for k in data}) != 1 and data:
                        incomplete()
            except DatabaseError:
                incomplete()
            raise
        return Response(self.output({**after, "user": profile}))

    def delete(self, request, pk):
        before = self.snapshot(self.get_row(pk))
        self.identity(request, pk=pk)
        with transaction.atomic():
            count, _ = self.model.objects.filter(**before).delete()
            if count != 1:
                conflict("Academic record changed. Reload before deleting.")
        try:
            self.identity(request, "DELETE", pk=pk)
        except IdentityFailure as exc:
            if exc.status_code == 404:
                # Another request already removed the identity; both rows are absent.
                return Response(status=204)
            if exc.uncertain:
                # A read resolves a lost DELETE response without replaying the write.
                try:
                    self.identity(request, pk=pk)
                except IdentityFailure as lookup:
                    if lookup.status_code == 404:
                        return Response(status=204)
                    incomplete()
            try:
                with transaction.atomic():
                    self.model.objects.create(**before)
            except DatabaseError:
                incomplete()
            raise exc
        return Response(status=204)


class StudentProfileView(CompositeView):
    kind = "students"


class LecturerProfileView(CompositeView):
    kind = "lecturers"
