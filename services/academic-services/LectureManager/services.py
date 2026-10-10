"""Lecturer business operations within academic-service."""

from django.db import IntegrityError, transaction

from DeparmentManager.models import Department

from .models import Lecturer


class BusinessValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(str(errors))


def _validate_department(data):
    department_id = data.get("department_id")
    if department_id is not None and not Department.objects.filter(pk=department_id).exists():
        raise BusinessValidationError({"department_id": "Department does not exist."})


def list_lecturers():
    return Lecturer.objects.all()


def get_lecturer(lecturer_id):
    return Lecturer.objects.get(pk=lecturer_id)


def create_lecturer(validated_data):
    _validate_department(validated_data)
    try:
        with transaction.atomic():
            if Lecturer.objects.filter(pk=validated_data["lecturer_id"]).exists():
                raise BusinessValidationError({"lecturer_id": "Lecturer already exists."})
            return Lecturer.objects.create(**validated_data)
    except IntegrityError as exc:
        raise BusinessValidationError({
            "lecturer_id": "Cannot create lecturer. Use a unique, existing user ID and valid references."
        }) from exc


def update_lecturer(lecturer_id, validated_data):
    obj = get_lecturer(lecturer_id)
    if validated_data.get("lecturer_id", obj.lecturer_id) != obj.lecturer_id:
        raise BusinessValidationError({"lecturer_id": "Lecturer ID cannot be changed."})
    _validate_department(validated_data)
    try:
        with transaction.atomic():
            if "department_id" in validated_data:
                obj.department_id = validated_data["department_id"]
                obj.save(update_fields=["department"])
    except IntegrityError as exc:
        raise BusinessValidationError({"department_id": "Cannot update lecturer with these references."}) from exc
    return obj


def delete_lecturer(lecturer_id):
    obj = get_lecturer(lecturer_id)
    try:
        with transaction.atomic():
            obj.delete()
    except IntegrityError as exc:
        raise BusinessValidationError({"lecturer_id": "Lecturer is referenced by other records and cannot be deleted."}) from exc
