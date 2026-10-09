from django.db import models

from MajorManager.models import Major


class SubMajor(models.Model):
    sub_major_id = models.CharField(db_column="SpecializationId", primary_key=True, max_length=255)
    name = models.TextField(db_column="SpecializationName", blank=True, null=True)
    major = models.ForeignKey(Major, db_column="MajorId", on_delete=models.DO_NOTHING, related_name="sub_majors", blank=True, null=True, db_constraint=False)

    class Meta:
        managed = False
        db_table = "Specializations"
        ordering = ["sub_major_id"]
