from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from .models import Department
from .serializers import DepartmentRequestDTO, DepartmentResponseDTO


class DepartmentListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = DepartmentRequestDTO

    def get(self, request):
        data = DepartmentResponseDTO(Department.objects.all(), many=True).data
        return Response(data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        department = Department.objects.create(**dto.validated_data)
        return Response(DepartmentResponseDTO.from_department(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = DepartmentRequestDTO

    def get_object(self):
        return get_object_or_404(Department, pk=self.kwargs["pk"])

    def get(self, request, pk):
        return Response(DepartmentResponseDTO.from_department(self.get_object()).data)

    def put(self, request, pk):
        return self._update(request, partial=False)

    def patch(self, request, pk):
        return self._update(request, partial=True)

    def _update(self, request, partial):
        department = self.get_object()
        dto = self.get_serializer(department, data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        for field, value in dto.validated_data.items():
            setattr(department, field, value)
        department.save()
        return Response(DepartmentResponseDTO.from_department(department).data)

    def delete(self, request, pk):
        department = self.get_object()
        try:
            department.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete a department that has majors."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
