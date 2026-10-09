from django.urls import path
from .views import SubMajorDetailView, SubMajorListCreateView

urlpatterns = [
    path("sub-majors/", SubMajorListCreateView.as_view(), name="sub-major-list"),
    path("sub-majors/<int:pk>/", SubMajorDetailView.as_view(), name="sub-major-detail"),
]
