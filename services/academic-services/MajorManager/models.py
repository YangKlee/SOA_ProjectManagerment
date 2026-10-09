from django.db import models

from DeparmentManager.models import Department


class Major(models.Model):
    major_id = models.CharField(db_column="MajorId", primary_key=True, max_length=255)
    name = models.TextField(db_column="MajorName", blank=True, null=True)
    department = models.ForeignKey(Department, db_column="FacultyId", on_delete=models.DO_NOTHING, related_name="majors", blank=True, null=True, db_constraint=False)

    class Meta:
        managed = False
        db_table = "Majors"
        ordering = ["major_id"]

    def __str__(self):
        return f"{self.major_id} - {self.name}"
