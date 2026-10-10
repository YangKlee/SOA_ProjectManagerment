"""SubMajor business operations within academic-service."""

from MajorManager.models import Major
from .models import SubMajor


class BusinessValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(str(errors))


def _validate(data):
    major_id = data.get("major_id")
    if major_id is not None and not Major.objects.filter(pk=major_id).exists():
        raise BusinessValidationError({"major_id": "Major does not exist."})


def list_sub_majors():
    return SubMajor.objects.all()


def get_sub_major(record_id):
    return SubMajor.objects.get(pk=record_id)


def create_sub_major(validated_data):
    _validate(validated_data)
    return SubMajor.objects.create(**validated_data)


def update_sub_major(record_id, validated_data):
    obj = get_sub_major(record_id)
    _validate(validated_data)
    for field, value in validated_data.items():
        setattr(obj, field, value)
    obj.save()
    return obj


def delete_sub_major(record_id):
    obj = get_sub_major(record_id)
    obj.delete()
