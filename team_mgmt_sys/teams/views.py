import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
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
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = TeamDetailSerializer(team)
        logger.info(f"Team detail fetched by {request.user.username}")
        return Response(serializer.data)


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

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_404_NOT_FOUND
            )

        if user in team.members.all() or user == team.created_by:
            return Response(
                {"non_field_errors": ["User Already in Team"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team.members.add(user)
        team.save()

        logger.info(
            f"User {user.username} added to team {team.name} by {request.user.username}"
        )
        return Response({"username": username}, status=status.HTTP_200_OK)


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

        serializer = RemoveMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]

        user = get_object_or_404(User, username=username)

        if user == team.created_by:
            return Response(
                {"detail": "Cannot remove the creator of the team."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user not in team.members.all():
            return Response(
                {"detail": "User is not a member of the team."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_404_NOT_FOUND
            )

        if user == team.created_by:
            return Response(
                {"non_field_errors": ["Cannot Remove team Creator"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user not in team.members.all():
            return Response(
                {"non_field_errors": ["User is not the member of team"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team.members.remove(user)
        team.save()

        logger.info(
            f"User {user.username} removed from team {team.name} by {request.user.username}"
        )
        return Response({"username": username}, status=status.HTTP_200_OK)


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
            tasks = Task.objects.filter(assigned_to=request.user)
            completed_tasks = tasks.filter(completed=True)
            incomplete_tasks = tasks.filter(completed=False)

            completed_serializer = TaskDetailSerializer(completed_tasks, many=True)
            incomplete_serializer = TaskDetailSerializer(incomplete_tasks, many=True)

            response_data = {
                "completed_task": completed_serializer.data,
                "incomplete_task": incomplete_serializer.data,
            }

            response_serializer = TaskListResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            logger.info(f"Tasks list fetched by {request.user.username}")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
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
        completed = serializer.validated_data["completed"]

        task.completed = completed
        task.save()

        logger.info(
            f"Task status updated by {request.user.username} for task {task.title}"
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)
