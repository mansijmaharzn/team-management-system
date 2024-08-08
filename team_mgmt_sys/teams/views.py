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
                response=TeamDetailSerializer, description="Successful Team Creation"
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Team Creation"
            ),
        },
    )
    def post(self, request, format=None):
        serializer = TeamDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            logger.info(f"Team created by {request.user.username}")
            return Response(
                {
                    "message": "Team Created Successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        logger.warning(
            f"Failed to create team by {request.user.username}: {serializer.errors}"
        )
        return Response(
            {"message": "Error Creating Team", "data": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


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
            return Response(
                {"message": "Successfully Fetched Team List", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch teams list by {request.user.username}: {str(e)}"
            )
            return Response(
                {
                    "message": "Failed to Fetch Team List",
                    "data": {"non_field_errors": [str(e)]},
                },
                status=status.HTTP_400_BAD_REQUEST,
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
    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        try:
            team = get_object_or_404(Team, pk=pk)
            self.check_object_permissions(request, team)

            serializer = TeamDetailSerializer(team)
            logger.info(f"Team detail fetched by {request.user.username}")
            return Response(
                {
                    "message": "Team Detail Fetched Successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch team detail by {request.user.username}: {str(e)}"
            )
            return Response(
                {
                    "message": "Failed to Fetch Team Detail",
                    "data": {"non_field_errors": [str(e)]},
                },
                status=status.HTTP_400_BAD_REQUEST,
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
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = AddMemberSerializer(data=request.data, context={"team": team})
        if serializer.is_valid():
            username = serializer.save()
            logger.info(
                f"User {username} added to team {team.name} by {request.user.username}"
            )
            return Response(
                {
                    "message": "User added to the team successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Error adding user to the team", "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


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
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = RemoveMemberSerializer(data=request.data, context={"team": team})

        if serializer.is_valid():
            username = serializer.save()
            logger.info(
                f"User {username} removed from team {team.name} by {request.user.username}"
            )
            return Response(
                {
                    "message": "User removed from the team successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "message": "Error removing user from the team",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class TaskCreateAPIView(APIView):
    """
    API View to create tasks associated with a specific team.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=TaskDetailSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskDetailSerializer, description="Successful Task Creation"
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

            serializer.save(team=team)
            logger.info(f"Task created by {request.user.username} in team {team.name}")
            return Response(
                {"message": "Task Creation Successsful", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        logger.warning(
            f"Failed to create task by {request.user.username} in team: {serializer.errors}"
        )
        return Response(
            {"message": "Task Creation Failed", "data": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


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
            return Response(
                {"message": "Task List Fetched Successfully", "data": response_data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch tasks list by {request.user.username}: {str(e)}"
            )
            return Response(
                {
                    "message": "Failed to Fetch Task List",
                    "data": {"non_field_errors": [str(e)]},
                },
                status=status.HTTP_400_BAD_REQUEST,
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
                response=TaskStatusUpdateSerializer,
                description="Successful Task Status Update",
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer, description="Failed Task Status Update"
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(request, task)

        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_task = serializer.update(task, serializer.validated_data)

        logger.info(
            f"Task status updated by {request.user.username} for task {updated_task.title}"
        )
        return Response(
            {"message": "Task Updated Successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class TaskUpdateAssigneUserAPIView(APIView):
    """
    API View to update assigned user of a task.
    """

    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]

    @extend_schema(
        request=TaskAssignedUserUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskAssignedUserUpdateSerializer,
                description="Successful Task Assigned to User Update",
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
    def patch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
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
        return Response(
            {
                "message": "Successfully Assigned Task to the user",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


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
    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        try:
            team = get_object_or_404(Team, pk=pk)
            self.check_object_permissions(request, team)

            tasks = Task.objects.filter(team=team)
            serializer = TaskListResponseSerializer(
                context={"user": request.user, "tasks": tasks}
            )
            response_data = serializer.to_representation()

            logger.info(f"Tasks list fetched by {request.user.username}")
            return Response(
                {"message": "Successfully Fetched Tasks", "data": response_data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch tasks list by {request.user.username}: {str(e)}"
            )
            return Response(
                {
                    "message": "Failed to Fetch Tasks",
                    "data": {"non_field_errors": [str(e)]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
