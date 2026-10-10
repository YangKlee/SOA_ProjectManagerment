"""Major business operations within academic-service."""

from DeparmentManager.models import Department
from .models import Major


class BusinessValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(str(errors))


def _validate(data):
    department_id = data.get("department_id")
    if department_id is not None and not Department.objects.filter(pk=department_id).exists():
        raise BusinessValidationError({"department_id": "Department does not exist."})


def list_majors():
    return Major.objects.all()


def get_major(record_id):
    return Major.objects.get(pk=record_id)


def create_major(validated_data):
    _validate(validated_data)
    return Major.objects.create(**validated_data)


def update_major(record_id, validated_data):
    obj = get_major(record_id)
    _validate(validated_data)
    for field, value in validated_data.items():
        setattr(obj, field, value)
    obj.save()
    return obj


def delete_major(record_id):
    obj = get_major(record_id)
    obj.delete()
