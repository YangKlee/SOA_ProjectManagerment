from django.db import models

from DeparmentManager.models import Department


class Lecturer(models.Model):
    # The user reference is an opaque ID; academic-service never queries Users.
    lecturer_id = models.TextField(db_column="LecturerId", primary_key=True)
    department = models.ForeignKey(
        Department,
        db_column="FacultyId",
        on_delete=models.DO_NOTHING,
        related_name="lecturers",
        blank=True,
        null=True,
        db_constraint=False,
    )

    class Meta:
        managed = False
        db_table = "Lecturers"
        ordering = ["lecturer_id"]
