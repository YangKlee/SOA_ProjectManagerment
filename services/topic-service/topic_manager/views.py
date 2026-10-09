from rest_framework.generics import GenericAPIView,get_object_or_404
from rest_framework.permissions import AllowAny,BasePermission,SAFE_METHODS
from rest_framework.response import Response
from .models import Topic
from .serializers import TopicRequestDTO,TopicResponseDTO
class RoleOneWrite(BasePermission):
 def has_permission(self,r,v): return bool(r.user and r.user.is_authenticated and (r.method in SAFE_METHODS or (r.auth and r.auth.get('role')==1)))
class HealthView(GenericAPIView):
 permission_classes=[AllowAny]
 def get(self,r): return Response({'status':'ok','service':'topic-service'})
class TopicListCreateView(GenericAPIView):
 permission_classes=[RoleOneWrite];serializer_class=TopicRequestDTO
 def get(self,r): return Response(TopicResponseDTO(Topic.objects.all(),many=True).data)
 def post(self,r):
  s=self.get_serializer(data=r.data);s.is_valid(raise_exception=True);o=Topic.objects.create(**s.validated_data);return Response(TopicResponseDTO(o).data,status=201)
class TopicDetailView(TopicListCreateView):
 def obj(self):return get_object_or_404(Topic,pk=self.kwargs['pk'])
 def get(self,r,pk):return Response(TopicResponseDTO(self.obj()).data)
 def patch(self,r,pk):
  o=self.obj();s=self.get_serializer(o,data=r.data,partial=True);s.is_valid(raise_exception=True);[setattr(o,k,v) for k,v in s.validated_data.items()];o.save();return Response(TopicResponseDTO(o).data)
 def delete(self,r,pk):self.obj().delete();return Response(status=204)
