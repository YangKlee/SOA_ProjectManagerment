"""Student business operations within academic-service."""

from MajorManager.models import Major
from SubMajorManager.models import SubMajor
from .models import Student


class BusinessValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(str(errors))


def _validate(data):
    major_id = data.get("major_id")
    sub_major_id = data.get("sub_major_id")
    if not Major.objects.filter(pk=major_id).exists():
        raise BusinessValidationError({"major_id": "Major does not exist."})
    if sub_major_id and not SubMajor.objects.filter(pk=sub_major_id, major_id=major_id).exists():
        raise BusinessValidationError({"sub_major_id": "Sub-major must belong to the selected major."})


def list_students():
    return Student.objects.all()


def get_student(record_id):
    return Student.objects.get(pk=record_id)


def create_student(validated_data):
    _validate(validated_data)
    return Student.objects.create(**validated_data)


def update_student(record_id, validated_data):
    obj = get_student(record_id)
    state = {field: getattr(obj, field) for field in ['major_id', 'sub_major_id']}
    state.update(validated_data)
    _validate(state)
    for field, value in validated_data.items():
        setattr(obj, field, value)
    obj.save()
    return obj


def delete_student(record_id):
    obj = get_student(record_id)
    obj.delete()
