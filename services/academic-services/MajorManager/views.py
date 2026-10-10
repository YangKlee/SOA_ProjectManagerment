from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from . import services
from .models import Major
from .serializers import MajorRequestDTO, MajorResponseDTO


def _call_service(operation, *args):
    try:
        return operation(*args)
    except Major.DoesNotExist as exc:
        raise NotFound("Major not found.") from exc
    except services.BusinessValidationError as exc:
        raise ValidationError(exc.errors) from exc


class MajorListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = MajorRequestDTO

    def get(self, request):
        records = services.list_majors()
        return Response(MajorResponseDTO(records, many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.create_major, dto.validated_data)
        return Response(MajorResponseDTO.from_major(obj).data, status=201)


class MajorDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = MajorRequestDTO

    def get(self, request, pk):
        obj = _call_service(services.get_major, pk)
        return Response(MajorResponseDTO.from_major(obj).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        dto = self.get_serializer(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.update_major, pk, dto.validated_data)
        return Response(MajorResponseDTO.from_major(obj).data)

    def delete(self, request, pk):
        _call_service(services.delete_major, pk)
        return Response(status=204)
