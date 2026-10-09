from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from .permissions import ReadOnlyOrRoleOneWrite


class DatabaseFirstListCreateView(GenericAPIView):
    permission_classes = [ReadOnlyOrRoleOneWrite]
    model = None
    response_dto = None

    def get(self, request):
        return Response(self.response_dto(self.model.objects.all(), many=True).data)

    def post(self, request):
        dto = self.get_serializer(data=request.data)
        dto.is_valid(raise_exception=True)
        obj = self.model.objects.create(**dto.validated_data)
        return Response(self.response_dto.from_object(obj).data, status=201)


class DatabaseFirstDetailView(DatabaseFirstListCreateView):
    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs["pk"])

    def get(self, request, pk):
        return Response(self.response_dto.from_object(self.get_object()).data)

    def put(self, request, pk):
        return self._update(request, False)

    def patch(self, request, pk):
        return self._update(request, True)

    def _update(self, request, partial):
        obj = self.get_object()
        dto = self.get_serializer(obj, data=request.data, partial=partial)
        dto.is_valid(raise_exception=True)
        for field, value in dto.validated_data.items():
            setattr(obj, field, value)
        obj.save()
        return Response(self.response_dto.from_object(obj).data)

    def delete(self, request, pk):
        self.get_object().delete()
        return Response(status=204)
