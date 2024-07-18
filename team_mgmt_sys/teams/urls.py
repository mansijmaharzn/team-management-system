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


urlpatterns = [
    path("create/", TeamCreateAPIView.as_view(), name="team-create"),
    path("my-teams/", TeamListAPIView.as_view(), name="team-show"),
    path("<int:pk>/team-detail/", TeamDetailAPIView.as_view(), name="team-detail"),
    path("<int:pk>/add-member/", AddMemberAPIView.as_view(), name="add_member"),
    path(
        "<int:pk>/remove-member/", RemoveMemberAPIView.as_view(), name="remove_member"
    ),
    path("create-tasks/", TaskCreateAPIView.as_view(), name="task-create"),
    path("my-tasks/", TaskListAPIView.as_view(), name="task-show"),
    path(
        "my-tasks/<int:pk>/update/",
        TaskStatusUpdateAPIView.as_view(),
        name="task-update",
    ),
    path("tasks/<int:pk>/details/", TeamTaskStatusView.as_view(), name="task-details"),
    path(
        "tasks/<int:pk>/assign/",
        TaskUpdateAssigneUserAPIView.as_view(),
        name="task-assign-user",
    ),
]
