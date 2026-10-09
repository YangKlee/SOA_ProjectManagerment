from django.db import models

from MajorManager.models import Major
from SubMajorManager.models import SubMajor


class Student(models.Model):
    student_code = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    major = models.ForeignKey(Major, on_delete=models.PROTECT, related_name="students")
    sub_major = models.ForeignKey(SubMajor, on_delete=models.PROTECT, related_name="students", null=True, blank=True)

    class Meta:
        ordering = ["student_code"]
