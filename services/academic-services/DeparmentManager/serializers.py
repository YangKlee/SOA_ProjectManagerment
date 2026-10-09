from rest_framework import serializers

from .models import Department


class DepartmentRequestDTO(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=255)

    def validate_code(self, value):
        queryset = Department.objects.filter(code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A department with this code already exists.")
        return value

    def validate_name(self, value):
        queryset = Department.objects.filter(name=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A department with this name already exists.")
        return value


class DepartmentResponseDTO(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)

    @classmethod
    def from_department(cls, department):
        return cls({"id": department.id, "code": department.code, "name": department.name})
