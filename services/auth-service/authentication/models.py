from django.db import models


class Users(models.Model):
    """Auth-owned unmanaged mapping of the existing Users table."""

    userid = models.TextField(db_column="UserId", primary_key=True)
    lastname = models.TextField(db_column="LastName", blank=True, null=True)
    firstname = models.TextField(db_column="FirstName", blank=True, null=True)
    gender = models.IntegerField(db_column="Gender", blank=True, null=True)
    dateofbirth = models.TextField(db_column="DateOfBirth", blank=True, null=True)
    password = models.TextField(db_column="Password")
    email = models.TextField(db_column="Email", unique=True)
    phone = models.TextField(db_column="Phone", unique=True)
    role = models.IntegerField(db_column="Role")
    status = models.IntegerField(db_column="Status", blank=True, null=True)
    createdat = models.TextField(db_column="CreatedAt", blank=True, null=True)
    updatedat = models.TextField(db_column="UpdatedAt", blank=True, null=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        managed = False
        db_table = "Users"
