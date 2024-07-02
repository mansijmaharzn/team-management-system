from django.urls import path

from teams.views import TeamCreateAPIView, TeamListAPIView

urlpatterns = [
    path('create/', TeamCreateAPIView.as_view(), name='team-create'),
    path('my-teams/', TeamListAPIView.as_view(), name='team-show'),
]