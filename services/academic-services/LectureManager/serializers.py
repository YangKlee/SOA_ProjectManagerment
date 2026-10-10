from rest_framework import serializers


class LecturerRequestDTO(serializers.Serializer):
    lecturer_id = serializers.CharField()
    department_id = serializers.CharField(required=False, allow_null=True)


class LecturerResponseDTO(serializers.Serializer):
    lecturer_id = serializers.CharField(read_only=True)
    department_id = serializers.CharField(read_only=True, allow_null=True)

    @classmethod
    def from_lecturer(cls, obj):
        return cls({
            "lecturer_id": obj.lecturer_id,
            "department_id": obj.department_id,
        })
