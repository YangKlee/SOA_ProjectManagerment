from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from security.permissions import ReadOnlyOrRoleOneWrite

from . import services
from .models import SubMajor
from .serializers import SubMajorRequestDTO, SubMajorResponseDTO


def _call_service(operation, *args):
    try:
        return operation(*args)
    except SubMajor.DoesNotExist as exc:
        raise NotFound("SubMajor not found.") from exc
    except services.BusinessValidationError as exc:
        raise ValidationError(exc.errors) from exc


class SubMajorListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = SubMajorRequestDTO

    def get(self, request):
        records = services.list_sub_majors()
        return Response(SubMajorResponseDTO(records, many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.create_sub_major, dto.validated_data)
        return Response(SubMajorResponseDTO.from_sub_major(obj).data, status=201)


class SubMajorDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = SubMajorRequestDTO

    def get(self, request, pk):
        obj = _call_service(services.get_sub_major, pk)
        return Response(SubMajorResponseDTO.from_sub_major(obj).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        dto = self.get_serializer(data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        obj = _call_service(services.update_sub_major, pk, dto.validated_data)
        return Response(SubMajorResponseDTO.from_sub_major(obj).data)

    def delete(self, request, pk):
        _call_service(services.delete_sub_major, pk)
        return Response(status=204)
