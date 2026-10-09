from rest_framework import serializers

from DeparmentManager.models import Department
from .models import Major


class MajorRequestDTO(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=255)
    department_id = serializers.IntegerField()

    def validate_code(self, value):
        query = Major.objects.filter(code=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("A major with this code already exists.")
        return value

    def validate_name(self, value):
        query = Major.objects.filter(name=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("A major with this name already exists.")
        return value

    def validate_department_id(self, value):
        if not Department.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Department does not exist.")
        return value


class MajorResponseDTO(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)

    @classmethod
    def from_major(cls, major):
        return cls({"id": major.id, "code": major.code, "name": major.name, "department_id": major.department_id})
