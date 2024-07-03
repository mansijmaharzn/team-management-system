from django.urls import path

from teams.views import TeamCreateAPIView, TeamListAPIView, AddMemberAPIView, RemoveMemberAPIView, TaskCreateAPIView, TaskListAPIView

urlpatterns = [
    path('create/', TeamCreateAPIView.as_view(), name='team-create'),
    path('my-teams/', TeamListAPIView.as_view(), name='team-show'),
    path('<int:pk>/add-member/', AddMemberAPIView.as_view(), name='add_member'),
    path('<int:pk>/remove-member/', RemoveMemberAPIView.as_view(), name="remove_member"),
    path('<int:team_id>/tasks/', TaskCreateAPIView.as_view(), name='task-create'),
    path('my-tasks/', TaskListAPIView.as_view(), name='task-show'),
]