from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from . import services
from .models import Student
from .serializers import StudentRequestDTO, StudentResponseDTO


def _call_service(operation, *args):
    try:
        return operation(*args)
    except Student.DoesNotExist as exc:
        raise NotFound("Student not found.") from exc
    except services.BusinessValidationError as exc:
        raise ValidationError(exc.errors) from exc


class StudentListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = StudentRequestDTO

    def get(self, request):
        records = services.list_students()
        return Response(StudentResponseDTO(records, many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.create_student, dto.validated_data)
        return Response(StudentResponseDTO.from_student(obj).data, status=201)


class StudentDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = StudentRequestDTO

    def get(self, request, pk):
        obj = _call_service(services.get_student, pk)
        return Response(StudentResponseDTO.from_student(obj).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        dto = self.get_serializer(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.update_student, pk, dto.validated_data)
        return Response(StudentResponseDTO.from_student(obj).data)

    def delete(self, request, pk):
        _call_service(services.delete_student, pk)
        return Response(status=204)
