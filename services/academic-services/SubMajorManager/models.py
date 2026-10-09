from django.db import models

from MajorManager.models import Major


class SubMajor(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, unique=True)
    major = models.ForeignKey(Major, on_delete=models.PROTECT, related_name="sub_majors")

    class Meta:
        ordering = ["code"]
