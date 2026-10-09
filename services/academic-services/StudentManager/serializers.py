from rest_framework import serializers
from MajorManager.models import Major
from SubMajorManager.models import SubMajor
class StudentRequestDTO(serializers.Serializer):
    student_id = serializers.CharField(max_length=255)
    major_id = serializers.CharField()
    sub_major_id = serializers.CharField(required=False, allow_null=True)
    accumulated_credits = serializers.IntegerField()
    gpa = serializers.FloatField()
    def validate(self, attrs):
        major_id = attrs.get("major_id", getattr(self.instance, "major_id", None)); sub_major_id = attrs.get("sub_major_id", getattr(self.instance, "sub_major_id", None))
        if not Major.objects.filter(pk=major_id).exists(): raise serializers.ValidationError({"major_id": "Major does not exist."})
        if sub_major_id and not SubMajor.objects.filter(pk=sub_major_id, major_id=major_id).exists(): raise serializers.ValidationError({"sub_major_id": "Sub-major must belong to the selected major."})
        return attrs
class StudentResponseDTO(serializers.Serializer):
    student_id = serializers.CharField(read_only=True); major_id = serializers.CharField(read_only=True); sub_major_id = serializers.CharField(read_only=True, allow_null=True); accumulated_credits = serializers.IntegerField(read_only=True); gpa = serializers.FloatField(read_only=True)
    @classmethod
    def from_student(cls, obj): return cls({field: getattr(obj, field) for field in ["student_id", "major_id", "sub_major_id", "accumulated_credits", "gpa"]})
