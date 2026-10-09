from django.urls import path
from .views import MajorDetailView, MajorListCreateView

urlpatterns = [
    path("majors/", MajorListCreateView.as_view(), name="major-list"),
    path("majors/<int:pk>/", MajorDetailView.as_view(), name="major-detail"),
]
