from rest_framework import serializers
class DepartmentRequestDTO(serializers.Serializer):
    department_id = serializers.CharField(max_length=255)
    name = serializers.CharField()
class DepartmentResponseDTO(serializers.Serializer):
    department_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    @classmethod
    def from_department(cls, obj): return cls({"department_id": obj.department_id, "name": obj.name})
