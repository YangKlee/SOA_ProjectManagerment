from rest_framework import serializers
class MajorRequestDTO(serializers.Serializer):
    major_id = serializers.CharField(max_length=255)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department_id = serializers.CharField(required=False, allow_null=True)
class MajorResponseDTO(serializers.Serializer):
    major_id = serializers.CharField(read_only=True); name = serializers.CharField(read_only=True, allow_null=True); department_id = serializers.CharField(read_only=True, allow_null=True)
    @classmethod
    def from_major(cls, obj): return cls({"major_id": obj.major_id, "name": obj.name, "department_id": obj.department_id})
