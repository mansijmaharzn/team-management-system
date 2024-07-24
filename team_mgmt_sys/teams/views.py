import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from teams.permissions import IsTeamCreator, IsTeamMemberOrCreator, IsAssignedToTask
from teams.models import Team, Task
from teams.serializers import (
    TeamSerializer,
    TeamDetailSerializer,
    AddMemberSerializer,
    RemoveMemberSerializer,
    TaskSerializer,
    TaskDetailSerializer,
    TaskListResponseSerializer,
    CustomErrorSerializer,
    TaskStatusUpdateSerializer,
    TaskAssignedUserUpdateSerializer,
)


logger = logging.getLogger(__name__)


class TeamCreateAPIView(APIView):
    """
    API View to create a team.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=TeamDetailSerializer,
        responses={
            200: OpenApiResponse(
                response=TeamSerializer, description="Successful Team Creation"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Team Creation"
            ),
        },
    )
    def post(self, request, format=None):
        detail_serializer = TeamDetailSerializer(data=request.data)
        if detail_serializer.is_valid():
            team = detail_serializer.save(created_by=self.request.user)
            logger.info(f"Team created by {request.user.username}")
            response_serializer = TeamSerializer(team)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            f"Failed to create team by {request.user.username}: {detail_serializer.errors}"
        )
        return Response(detail_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamListAPIView(APIView):
    """
    API View to list teams associated with the authenticated user (member/creator of).
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TeamDetailSerializer(many=True),
                description="Successful Team List Fetch",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Team List Fetch"
            ),
        }
    )
    def get(self, request, format=None):
        try:
            teams = Team.objects.filter(
                Q(members=request.user) | Q(created_by=request.user)
            ).distinct()
            serializer = TeamSerializer(teams, many=True)
            logger.info(f"Teams list fetched by {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.warning(
                f"Failed to fetch teams list by {request.user.username}: {str(e)}"
            )
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST
            )


class TeamDetailAPIView(APIView):
    """
    API View to get detail information of a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamMemberOrCreator]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TeamDetailSerializer,
                description="Successful Team Detail Fetch",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Team Detail Fetch"
            ),
        }
    )
    def get(self, request, pk, format=None):
        try:
            team = get_object_or_404(Team, pk=pk)
            self.check_object_permissions(request, team)

            serializer = TeamDetailSerializer(team)
            logger.info(f"Team detail fetched by {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.warning(
                f"Failed to fetch team detail by {request.user.username}: {str(e)}"
            )
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST
            )


class AddMemberAPIView(APIView):
    """
    API View to add member to a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=AddMemberSerializer,
        responses={
            200: OpenApiResponse(
                response=AddMemberSerializer, description="Successful Member Addition"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="User Already in Team"
            ),
            404: OpenApiResponse(
                response=CustomErrorSerializer, description="User Not Found"
            ),
        },
    )
    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = AddMemberSerializer(data=request.data, context={"team": team})
        if serializer.is_valid():
            username = serializer.save()
            logger.info(
                f"User {username} added to team {team.name} by {request.user.username}"
            )
            return Response({"username": username}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveMemberAPIView(APIView):
    """
    API View to remove member from a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=AddMemberSerializer,
        responses={
            200: OpenApiResponse(
                response=RemoveMemberSerializer, description="Successful Member Removal"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description="User not in Team or Cannot Remove Creator",
            ),
            404: OpenApiResponse(
                response=CustomErrorSerializer, description="User Not Found"
            ),
        },
    )
    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = RemoveMemberSerializer(data=request.data, context={"team": team})

        if serializer.is_valid():
            username = serializer.save()
            logger.info(
                f"User {username} removed from team {team.name} by {request.user.username}"
            )
            return Response({"username": username}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskCreateAPIView(APIView):
    """
    API View to create tasks associated with a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=TaskDetailSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskSerializer, description="Successful Task Creation"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Task Creation"
            ),
        },
    )
    def post(self, request, format=None):
        serializer = TaskDetailSerializer(data=request.data)
        if serializer.is_valid():
            team = serializer.validated_data["team"]

            self.check_object_permissions(request, team)

            task = serializer.save(team=team)
            response_serializer = TaskSerializer(task)
            logger.info(f"Task created by {request.user.username} in team {team.name}")
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            f"Failed to create task by {request.user.username} in team: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskListAPIView(APIView):
    """
    API View to list tasks assigned to the authenticated user.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskListResponseSerializer,
                description="Successful Task List Fetch",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Task List Fetch"
            ),
        }
    )
    def get(self, request, format=None):
        try:
            serializer = TaskListResponseSerializer(context={"user": request.user})
            response_data = serializer.to_representation()

            logger.info(f"Tasks list fetched by {request.user.username}")
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(
                f"Failed to fetch tasks list by {request.user.username}: {str(e)}"
            )
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST
            )


class TaskStatusUpdateAPIView(APIView):
    """
    API View to change task status.
    """

    permission_classes = [permissions.IsAuthenticated, IsAssignedToTask]

    @extend_schema(
        request=TaskStatusUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskSerializer, description="Successful Task Status Update"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Task Status Update"
            ),
        },
    )
    def patch(self, request, pk, format=None):
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(request, task)

        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_task = serializer.update(task, serializer.validated_data)

        logger.info(
            f"Task status updated by {request.user.username} for task {updated_task.title}"
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


class TaskUpdateAssigneUserAPIView(APIView):
    """
    API View to update assigned user of a task.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=TaskAssignedUserUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskSerializer,
                description="Successful Task Assigned User Update",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description="Failed Task Assigned User Update",
            ),
            404: OpenApiResponse(
                response=CustomErrorSerializer, description="Task Not Found"
            ),
        },
    )
    def patch(self, request, pk, format=None):
        task = get_object_or_404(Task, pk=pk)
        team = get_object_or_404(Team, pk=task.team.pk)
        self.check_object_permissions(request, team)

        serializer = TaskAssignedUserUpdateSerializer(
            data=request.data, instance=task, partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_task = serializer.save()

        logger.info(
            f"Task assigned user updated by {request.user.username} for task {updated_task.title}"
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


class TeamTaskStatusView(APIView):
    """
    API View to get detail task infomation of a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskListResponseSerializer,
                description="Successful Task Detail Fetch",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Task Detail Fetch"
            ),
        }
    )
    def get(self, request, pk, format=None):
        try:
            team = get_object_or_404(Team, pk=pk)
            self.check_object_permissions(request, team)

            tasks = Task.objects.filter(team=team)
            serializer = TaskListResponseSerializer(
                context={"user": request.user, "tasks": tasks}
            )
            response_data = serializer.to_representation()

            logger.info(f"Tasks list fetched by {request.user.username}")
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(
                f"Failed to fetch tasks list by {request.user.username}: {str(e)}"
            )
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST
            )
