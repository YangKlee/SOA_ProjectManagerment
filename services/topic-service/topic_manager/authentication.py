from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.models import TokenUser


class TopicJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not isinstance(user_id, str) or not user_id.strip() or len(user_id) > 255:
            raise AuthenticationFailed("Token contains no valid user identity.")
        return TokenUser(validated_token)
