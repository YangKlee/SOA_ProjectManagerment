from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from security.permissions import ReadOnlyOrRoleOneWrite
from .models import Student
from .serializers import StudentRequestDTO, StudentResponseDTO


class StudentListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = StudentRequestDTO
    def get(self, request): return Response(StudentResponseDTO(Student.objects.all(), many=True).data)
    def post(self, request):
        dto = self.get_serializer(data=request.data); dto.is_valid(raise_exception=True)
        data = dto.validated_data
        obj = Student.objects.create(**{("major_id" if key == "major_id" else "sub_major_id" if key == "sub_major_id" else key): value for key, value in data.items()})
        return Response(StudentResponseDTO.from_student(obj).data, status=status.HTTP_201_CREATED)


class StudentDetailView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    serializer_class = StudentRequestDTO
    def get_object(self): return get_object_or_404(Student, pk=self.kwargs["pk"])
    def get(self, request, pk): return Response(StudentResponseDTO.from_student(self.get_object()).data)
    def put(self, request, pk): return self._update(request, False)
    def patch(self, request, pk): return self._update(request, True)
    def _update(self, request, partial):
        obj = self.get_object(); dto = self.get_serializer(obj, data=request.data, partial=partial); dto.is_valid(raise_exception=True)
        for field, value in dto.validated_data.items(): setattr(obj, field, value)
        obj.save(); return Response(StudentResponseDTO.from_student(obj).data)
    def delete(self, request, pk):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
