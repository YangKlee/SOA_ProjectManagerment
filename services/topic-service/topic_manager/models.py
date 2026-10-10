from django.db import models


class Topic(models.Model):
    topic_id = models.CharField(db_column="TopicId", primary_key=True, max_length=255)
    name = models.TextField(db_column="TopicName")
    description = models.TextField(db_column="Description", blank=True, null=True)
    file_url = models.TextField(db_column="FileUrl", blank=True, null=True)
    # IDs reference other services without importing their ORM models.
    major_id = models.CharField(db_column="MajorId", max_length=255)
    status = models.IntegerField(db_column="Status", blank=True, null=True)
    advisor_id = models.CharField(db_column="AdvisorId", max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(db_column="CreatedAt", blank=True, null=True)
    updated_at = models.DateTimeField(db_column="UpdatedAt", blank=True, null=True)
    updated_by = models.CharField(db_column="UpdatedBy", max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "Topics"
