from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from . import services
from .models import Department
from .serializers import DepartmentRequestDTO, DepartmentResponseDTO


def _call_service(operation, *args):
    try:
        return operation(*args)
    except Department.DoesNotExist as exc:
        raise NotFound("Department not found.") from exc


class DepartmentListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = DepartmentRequestDTO

    def get(self, request):
        departments = services.list_departments()
        return Response(DepartmentResponseDTO(departments, many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        department = services.create_department(dto.validated_data)
        return Response(
            DepartmentResponseDTO.from_department(department).data, status=201
        )


class DepartmentDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = DepartmentRequestDTO

    def get(self, request, pk):
        department = _call_service(services.get_department, pk)
        return Response(DepartmentResponseDTO.from_department(department).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        dto = self.get_serializer(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        department = _call_service(services.update_department, pk, dto.validated_data)
        return Response(DepartmentResponseDTO.from_department(department).data)

    def delete(self, request, pk):
        _call_service(services.delete_department, pk)
        return Response(status=204)
