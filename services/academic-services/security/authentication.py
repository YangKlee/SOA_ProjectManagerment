from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.models import TokenUser


class AcademicJWTAuthentication(JWTAuthentication):
    """Validate auth-service JWTs locally without accessing its database."""

    def get_user(self, validated_token):
        # Academic-service owns no Users model. TokenUser preserves the token
        # claims for authorization while avoiding any auth database lookup.
        return TokenUser(validated_token)
