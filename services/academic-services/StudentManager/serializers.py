from rest_framework import serializers
class StudentRequestDTO(serializers.Serializer):
    student_id = serializers.CharField(max_length=255)
    major_id = serializers.CharField()
    sub_major_id = serializers.CharField(required=False, allow_null=True)
    accumulated_credits = serializers.IntegerField()
    gpa = serializers.FloatField()
class StudentResponseDTO(serializers.Serializer):
    student_id = serializers.CharField(read_only=True); major_id = serializers.CharField(read_only=True); sub_major_id = serializers.CharField(read_only=True, allow_null=True); accumulated_credits = serializers.IntegerField(read_only=True); gpa = serializers.FloatField(read_only=True)
    @classmethod
    def from_student(cls, obj): return cls({field: getattr(obj, field) for field in ["student_id", "major_id", "sub_major_id", "accumulated_credits", "gpa"]})
