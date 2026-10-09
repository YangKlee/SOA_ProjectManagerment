from security.crud import DatabaseFirstDetailView, DatabaseFirstListCreateView
from .models import Major
from .serializers import MajorRequestDTO, MajorResponseDTO
MajorResponseDTO.from_object = MajorResponseDTO.from_major
class MajorListCreateView(DatabaseFirstListCreateView): model=Major; serializer_class=MajorRequestDTO; response_dto=MajorResponseDTO
class MajorDetailView(DatabaseFirstDetailView): model=Major; serializer_class=MajorRequestDTO; response_dto=MajorResponseDTO
