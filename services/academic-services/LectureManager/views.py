from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from . import services
from .models import Lecturer
from .serializers import LecturerRequestDTO, LecturerResponseDTO


def _call_service(operation, *args):
    try:
        return operation(*args)
    except Lecturer.DoesNotExist as exc:
        raise NotFound("Lecturer not found.") from exc
    except services.BusinessValidationError as exc:
        raise ValidationError(exc.errors) from exc


class LecturerListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = LecturerRequestDTO

    def get(self, request):
        return Response(LecturerResponseDTO(services.list_lecturers(), many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.create_lecturer, dto.validated_data)
        return Response(LecturerResponseDTO.from_lecturer(obj).data, status=201)


class LecturerDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = LecturerRequestDTO

    def get(self, request, pk):
        obj = _call_service(services.get_lecturer, pk)
        return Response(LecturerResponseDTO.from_lecturer(obj).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        dto = self.get_serializer(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.update_lecturer, pk, dto.validated_data)
        return Response(LecturerResponseDTO.from_lecturer(obj).data)

    def delete(self, request, pk):
        _call_service(services.delete_lecturer, pk)
        return Response(status=204)
