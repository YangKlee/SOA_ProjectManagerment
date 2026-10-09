from django.db import models

from DeparmentManager.models import Department


class Major(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="majors")

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"
