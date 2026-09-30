from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

def check_health(request):
    return JsonResponse({"status": "ok"}, status=status.HTTP_200_OK)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # xử lý login

        return Response({
            "message": "Login successfully"
        })
