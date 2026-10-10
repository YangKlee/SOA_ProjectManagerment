from hmac import compare_digest

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Users
from .serializers import (
    HealthResponseSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
    UserResponseSerializer,
)


class HealthView(APIView):
    """Public liveness endpoint for the API gateway and container checks."""

    permission_classes = [AllowAny]

    def get(self, request):
        payload = {"status": "ok", "service": "auth-service"}
        return Response(HealthResponseSerializer(payload).data, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_dto = LoginRequestSerializer(data=request.data)
        request_dto.is_valid(raise_exception=True)
        identifier = request_dto.validated_data["identifier"]
        password = request_dto.validated_data["password"]

        try:
            user = Users.objects.get(email=identifier)
        except Users.DoesNotExist:
            try:
                user = Users.objects.get(userid=identifier)
            except Users.DoesNotExist:
                user = None

        if user is None or not compare_digest(
            password.encode("utf-8"), user.password.encode("utf-8")
        ):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken()
        refresh["user_id"] = str(user.userid)
        refresh["email"] = user.email
        refresh["role"] = user.role

        response_dto = LoginResponseSerializer({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "token_type": "Bearer",
            "user": user,
        })
        return Response(response_dto.data, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_dto = TokenRefreshRequestSerializer(data=request.data)
        request_dto.is_valid(raise_exception=True)
        raw_refresh = request_dto.validated_data["refresh"]

        try:
            refresh = RefreshToken(raw_refresh)
            user_id = refresh.get("user_id")
            if user_id is None:
                raise TokenError("Token does not contain a user id.")
            Users.objects.get(userid=user_id)
        except (TokenError, Users.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response_dto = TokenRefreshResponseSerializer(
            {"access": str(refresh.access_token), "token_type": "Bearer"}
        )
        return Response(response_dto.data, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """Return the authenticated user's safe profile DTO."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserResponseSerializer(request.user).data, status=status.HTTP_200_OK)
