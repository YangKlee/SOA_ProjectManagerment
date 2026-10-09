from django.db import models

from MajorManager.models import Major
from SubMajorManager.models import SubMajor


class Student(models.Model):
    student_id = models.CharField(db_column="StudentId", primary_key=True, max_length=255)
    major = models.ForeignKey(Major, db_column="MajorId", on_delete=models.DO_NOTHING, related_name="students", db_constraint=False)
    sub_major = models.ForeignKey(SubMajor, db_column="SpecializationId", on_delete=models.DO_NOTHING, related_name="students", null=True, blank=True, db_constraint=False)
    accumulated_credits = models.IntegerField(db_column="AccumulatedCredits")
    gpa = models.FloatField(db_column="GPA")

    class Meta:
        managed = False
        db_table = "Students"
        ordering = ["student_id"]
