from rest_framework import serializers
from MajorManager.models import Major
from SubMajorManager.models import SubMajor
from .models import Student


class StudentRequestDTO(serializers.Serializer):
    student_code = serializers.CharField(max_length=30)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    major_id = serializers.IntegerField()
    sub_major_id = serializers.IntegerField(required=False, allow_null=True)

    def _unique(self, field, value):
        query = Student.objects.filter(**{field: value})
        if self.instance: query = query.exclude(pk=self.instance.pk)
        if query.exists(): raise serializers.ValidationError(f"A student with this {field} already exists.")
        return value

    def validate_student_code(self, value): return self._unique("student_code", value)
    def validate_email(self, value): return self._unique("email", value)
    def validate_major_id(self, value):
        if not Major.objects.filter(pk=value).exists(): raise serializers.ValidationError("Major does not exist.")
        return value
    def validate_sub_major_id(self, value):
        if value is not None and not SubMajor.objects.filter(pk=value).exists(): raise serializers.ValidationError("Sub-major does not exist.")
        return value

    def validate(self, attrs):
        major_id = attrs.get("major_id", self.instance.major_id if self.instance else None)
        sub_major_id = attrs.get("sub_major_id", self.instance.sub_major_id if self.instance else None)
        if sub_major_id and not SubMajor.objects.filter(pk=sub_major_id, major_id=major_id).exists():
            raise serializers.ValidationError({"sub_major_id": "Sub-major must belong to the selected major."})
        return attrs


class StudentResponseDTO(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    student_code = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(read_only=True)
    major_id = serializers.IntegerField(read_only=True)
    sub_major_id = serializers.IntegerField(read_only=True, allow_null=True)

    @classmethod
    def from_student(cls, obj):
        return cls({field: getattr(obj, field) for field in ["id", "student_code", "full_name", "email", "phone", "major_id", "sub_major_id"]})
