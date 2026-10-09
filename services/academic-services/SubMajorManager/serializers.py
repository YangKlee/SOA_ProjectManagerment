from rest_framework import serializers
from MajorManager.models import Major
class SubMajorRequestDTO(serializers.Serializer):
    sub_major_id = serializers.CharField(max_length=255)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    major_id = serializers.CharField(required=False, allow_null=True)
    def validate_major_id(self, value):
        if value is not None and not Major.objects.filter(pk=value).exists(): raise serializers.ValidationError("Major does not exist.")
        return value
class SubMajorResponseDTO(serializers.Serializer):
    sub_major_id = serializers.CharField(read_only=True); name = serializers.CharField(read_only=True, allow_null=True); major_id = serializers.CharField(read_only=True, allow_null=True)
    @classmethod
    def from_sub_major(cls, obj): return cls({"sub_major_id": obj.sub_major_id, "name": obj.name, "major_id": obj.major_id})
