from django.urls import path

from teams.views import (
    TeamCreateAPIView,
    TeamListAPIView,
    AddMemberAPIView,
    RemoveMemberAPIView,
    TaskCreateAPIView,
    TaskListAPIView,
    TeamDetailAPIView,
    TaskStatusUpdateAPIView,
    TeamTaskStatusView,
    TaskUpdateAssigneUserAPIView,
)

app_name = "teams"

urlpatterns = [
    # Team-related endpoints
    path("create/", TeamCreateAPIView.as_view(), name="team-create"),
    path("my-teams/", TeamListAPIView.as_view(), name="team-list"),
    path("<int:pk>/", TeamDetailAPIView.as_view(), name="team-detail"),
    path("<int:pk>/add-member/", AddMemberAPIView.as_view(), name="team-add-member"),
    path(
        "<int:pk>/remove-member/",
        RemoveMemberAPIView.as_view(),
        name="team-remove-member",
    ),
    # Task-related endpoints
    path("tasks/create/", TaskCreateAPIView.as_view(), name="task-create"),
    path("tasks/my-tasks/", TaskListAPIView.as_view(), name="task-list"),
    path(
        "tasks/<int:pk>/update-status/",
        TaskStatusUpdateAPIView.as_view(),
        name="task-update-status",
    ),
    path("tasks/<int:pk>/details/", TeamTaskStatusView.as_view(), name="task-details"),
    path(
        "tasks/<int:pk>/assign/",
        TaskUpdateAssigneUserAPIView.as_view(),
        name="task-assign-user",
    ),
]
