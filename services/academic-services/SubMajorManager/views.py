from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from security.permissions import ReadOnlyOrRoleOneWrite
from .models import SubMajor
from .serializers import SubMajorRequestDTO, SubMajorResponseDTO


class SubMajorListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = SubMajorRequestDTO

    def get(self, request):
        return Response(SubMajorResponseDTO(SubMajor.objects.all(), many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        data = dto.validated_data
        obj = SubMajor.objects.create(code=data["code"], name=data["name"], major_id=data["major_id"])
        return Response(SubMajorResponseDTO.from_sub_major(obj).data, status=status.HTTP_201_CREATED)


class SubMajorDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = SubMajorRequestDTO

    def get_object(self): return get_object_or_404(SubMajor, pk=self.kwargs["pk"])
    def get(self, request, pk): return Response(SubMajorResponseDTO.from_sub_major(self.get_object()).data)
    def put(self, request, pk): return self._update(request, False)
    def patch(self, request, pk): return self._update(request, True)

    def _update(self, request, partial):
        obj = self.get_object()
        dto = self.get_serializer(obj, data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        for field, value in dto.validated_data.items(): setattr(obj, "major_id" if field == "major_id" else field, value)
        obj.save()
        return Response(SubMajorResponseDTO.from_sub_major(obj).data)

    def delete(self, request, pk):
        try: self.get_object().delete()
        except ProtectedError:
            return Response({"detail": "Cannot delete a sub-major that has students."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
