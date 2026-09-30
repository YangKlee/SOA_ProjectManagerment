from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Users

def check_health(request):
    return JsonResponse({"status": "ok"}, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier")
        if identifier is None:
            identifier = request.data.get("email") or request.data.get("userid")
        password = request.data.get("password")

        if not isinstance(identifier, str) or not identifier.strip() or not isinstance(password, str) or not password:
            return Response(
                {"detail": "Email/userid and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = Users.objects.get(email=identifier.strip())
        except Users.DoesNotExist:
            try:
                user = Users.objects.get(userid=identifier.strip())
            except Users.DoesNotExist:
                user = None

        if user is None or not check_password(password, user.password):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken()
        refresh["user_id"] = str(user.userid)
        refresh["email"] = user.email
        refresh["role"] = user.role

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.data.get("refresh")
        if not isinstance(raw_refresh, str) or not raw_refresh:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        return Response({"access": str(refresh.access_token)})
