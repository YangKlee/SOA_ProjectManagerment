from rest_framework import serializers
from MajorManager.models import Major
from .models import SubMajor


class SubMajorRequestDTO(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=255)
    major_id = serializers.IntegerField()

    def _unique(self, field, value):
        query = SubMajor.objects.filter(**{field: value})
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError(f"A sub-major with this {field} already exists.")
        return value

    def validate_code(self, value): return self._unique("code", value)
    def validate_name(self, value): return self._unique("name", value)

    def validate_major_id(self, value):
        if not Major.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Major does not exist.")
        return value


class SubMajorResponseDTO(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    major_id = serializers.IntegerField(read_only=True)

    @classmethod
    def from_sub_major(cls, obj):
        return cls({"id": obj.id, "code": obj.code, "name": obj.name, "major_id": obj.major_id})
