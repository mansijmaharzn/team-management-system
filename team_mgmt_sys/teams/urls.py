from django.urls import path

from teams.views import TeamCreateAPIView, TeamListAPIView, AddMemberAPIView, RemoveMemberAPIView

urlpatterns = [
    path('create/', TeamCreateAPIView.as_view(), name='team-create'),
    path('my-teams/', TeamListAPIView.as_view(), name='team-show'),
    path('<int:pk>/add-member/', AddMemberAPIView.as_view(), name='add_member'),
    path('<int:pk>/remove-member/', RemoveMemberAPIView.as_view(), name="remove_member"),
]