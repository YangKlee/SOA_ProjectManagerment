from django.db import models


class Department(models.Model):
    department_id = models.CharField(db_column="FacultyId", primary_key=True, max_length=255)
    name = models.TextField(db_column="FacultyName")

    class Meta:
        managed = False
        db_table = "Faculties"
        ordering = ["department_id"]

    def __str__(self):
        return f"{self.department_id} - {self.name}"
