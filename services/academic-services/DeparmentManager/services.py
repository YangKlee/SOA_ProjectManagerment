"""Department operations within academic-service's data boundary."""

from .models import Department


def list_departments():
    return Department.objects.all()


def get_department(department_id):
    return Department.objects.get(pk=department_id)


def create_department(validated_data):
    return Department.objects.create(**validated_data)


def update_department(department_id, validated_data):
    department = get_department(department_id)
    for field, value in validated_data.items():
        setattr(department, field, value)
    department.save()
    return department


def delete_department(department_id):
    department = get_department(department_id)
    department.delete()
