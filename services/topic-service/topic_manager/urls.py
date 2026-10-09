from django.urls import path
from .views import HealthView, TopicDetailView, TopicListCreateView
urlpatterns=[path('health/',HealthView.as_view()),path('api/topics/',TopicListCreateView.as_view()),path('api/topics/<str:pk>/',TopicDetailView.as_view())]
