from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.models import TokenUser
class TopicJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token): return TokenUser(validated_token)
