from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .models import Users


class UsersJWTAuthentication(BaseAuthentication):
    """Authenticate bearer JWTs against the existing unmanaged Users table."""

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != b"bearer":
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Authorization header must be: Bearer <token>.")

        try:
            token = AccessToken(parts[1].decode("utf-8"))
            user_id = token.get("user_id")
            if user_id is None:
                raise AuthenticationFailed("Token does not contain a user id.")
            user = Users.objects.get(userid=user_id)
        except (TokenError, UnicodeDecodeError) as exc:
            raise AuthenticationFailed("Invalid or expired token.") from exc
        except Users.DoesNotExist as exc:
            raise AuthenticationFailed("User for this token no longer exists.") from exc

        return user, token

    def authenticate_header(self, request):
        return "Bearer"
