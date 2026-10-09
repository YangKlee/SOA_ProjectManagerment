from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response

from DeparmentManager.models import Department
from security.permissions import ReadOnlyOrRoleOneWrite
from .models import Major
from .serializers import MajorRequestDTO, MajorResponseDTO


class MajorListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = MajorRequestDTO

    def get(self, request):
        return Response(MajorResponseDTO(Major.objects.all(), many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        data = dto.validated_data
        major = Major.objects.create(code=data["code"], name=data["name"], department_id=data["department_id"])
        return Response(MajorResponseDTO.from_major(major).data, status=status.HTTP_201_CREATED)


class MajorDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = MajorRequestDTO

    def get_object(self):
        return get_object_or_404(Major, pk=self.kwargs["pk"])

    def get(self, request, pk):
        return Response(MajorResponseDTO.from_major(self.get_object()).data)

    def put(self, request, pk):
        return self._update(request, False)

    def patch(self, request, pk):
        return self._update(request, True)

    def _update(self, request, partial):
        major = self.get_object()
        dto = self.get_serializer(major, data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        for field, value in dto.validated_data.items():
            setattr(major, "department_id" if field == "department_id" else field, value)
        major.save()
        return Response(MajorResponseDTO.from_major(major).data)

    def delete(self, request, pk):
        try:
            self.get_object().delete()
        except ProtectedError:
            return Response({"detail": "Cannot delete a major that has dependent records."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
