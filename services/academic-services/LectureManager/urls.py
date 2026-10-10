from django.urls import path

from .views import LecturerDetailView, LecturerListCreateView


urlpatterns = [
    path("lecturers/", LecturerListCreateView.as_view(), name="lecturer-list"),
    path("lecturers/<str:pk>/", LecturerDetailView.as_view(), name="lecturer-detail"),
]
