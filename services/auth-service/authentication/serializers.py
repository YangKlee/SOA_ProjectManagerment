"""Request and response DTOs for the authentication API.

DRF serializers are used here as DTOs so the HTTP contract stays separate
from the unmanaged ``Users`` database model.  In particular, the password
field is never present in a response.
"""

from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()


class UserResponseSerializer(serializers.Serializer):
    """Public representation of a user; intentionally excludes password."""

    user_id = serializers.CharField(source="userid")
    first_name = serializers.CharField(source="firstname", allow_null=True)
    last_name = serializers.CharField(source="lastname", allow_null=True)
    gender = serializers.IntegerField(allow_null=True)
    date_of_birth = serializers.CharField(source="dateofbirth", allow_null=True)
    email = serializers.EmailField()
    phone = serializers.CharField()
    role = serializers.IntegerField()
    status = serializers.IntegerField(allow_null=True)
    created_at = serializers.CharField(source="createdat", allow_null=True)
    updated_at = serializers.CharField(source="updatedat", allow_null=True)


class LoginRequestSerializer(serializers.Serializer):
    """Accept an email, user ID, or the generic ``identifier`` field."""

    identifier = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(required=False)
    userid = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = attrs.get("identifier") or attrs.get("email") or attrs.get("userid")
        if not identifier:
            raise serializers.ValidationError(
                {"identifier": "Provide identifier, email, or userid."}
            )
        attrs["identifier"] = identifier
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    token_type = serializers.CharField()
    user = UserResponseSerializer()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=True)


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    token_type = serializers.CharField()
