from rest_framework import serializers
class SubMajorRequestDTO(serializers.Serializer):
    sub_major_id = serializers.CharField(max_length=255)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    major_id = serializers.CharField(required=False, allow_null=True)
class SubMajorResponseDTO(serializers.Serializer):
    sub_major_id = serializers.CharField(read_only=True); name = serializers.CharField(read_only=True, allow_null=True); major_id = serializers.CharField(read_only=True, allow_null=True)
    @classmethod
    def from_sub_major(cls, obj): return cls({"sub_major_id": obj.sub_major_id, "name": obj.name, "major_id": obj.major_id})
