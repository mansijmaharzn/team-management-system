import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse

from teams.permissions import IsTeamCreator
from teams.models import Team, Task
from teams.serializers import (
    TeamSerializer, 
    AddMemberSerializer, 
    RemoveMemberSerializer, 
    TaskSerializer,
    CustomErrorSerializer
)


logger = logging.getLogger(__name__)


class TeamCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

    @extend_schema(
            request=TeamSerializer,
            responses={
                200: OpenApiResponse(
                    response=TeamSerializer,
                    description='Successful Team Creation'
                ),
                400: OpenApiResponse(
                    response=CustomErrorSerializer,
                    description='Failed Team Creation'
                )
            }
    )
    def post(self, request, format=None):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            logger.info(f"Team created by {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(f"Failed to create team by {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TeamSerializer(many=True),
                description='Successful Team List Fetch'
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description='Failed Team List Fetch'
            )
        }
    )
    def get(self, request, format=None):
        try:
            teams = Team.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
            serializer = TeamSerializer(teams, many=True)
            logger.info(f"Teams list fetched by {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.warning(f"Failed to fetch teams list by {request.user.username}: {str(e)}")
            return Response({'non_field_errors': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        

class AddMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = AddMemberSerializer

    @extend_schema(
        request=AddMemberSerializer,
        responses={
            200: OpenApiResponse(
                response=TeamSerializer,
                description='Successful Member Addition'
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description='User Already in Team'
            ),
            404: OpenApiResponse(
                response=CustomErrorSerializer,
                description='User Not Found'
            )
        }
    )
    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response({'non_field_errors': [str(e)]}, status=status.HTTP_404_NOT_FOUND)

        if user in team.members.all() or user == team.created_by:
            return Response({'non_field_errors': ['User Already in Team']}, status=status.HTTP_400_BAD_REQUEST)
        
        team.members.add(user)
        team.save()

        serializer = TeamSerializer(team)
        logger.info(f"User {user.username} added to team {team.name} by {request.user.username}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RemoveMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = RemoveMemberSerializer

    @extend_schema(
        request=AddMemberSerializer,
        responses={
            200: OpenApiResponse(
                response=TeamSerializer,
                description='Successful Member Removal'
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description='User not in Team or Cannot Remove Creator'
            ),
            404: OpenApiResponse(
                response=CustomErrorSerializer,
                description='User Not Found'
            )
        }
    )
    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = RemoveMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        user = get_object_or_404(User, username=username)
        
        if user == team.created_by:
            return Response({'detail': 'Cannot remove the creator of the team.'}, status=status.HTTP_400_BAD_REQUEST)

        if user not in team.members.all():
            return Response({'detail': 'User is not a member of the team.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response({'non_field_errors': [str(e)]}, status=status.HTTP_404_NOT_FOUND)

        if user == team.created_by:
            return Response({'non_field_errors': ['Cannot Remove team Creator']}, status=status.HTTP_400_BAD_REQUEST)

        if user not in team.members.all():
            return Response({'non_field_errors': ['User is not the member of team']}, status=status.HTTP_400_BAD_REQUEST)

        team.members.remove(user)
        team.save()

        response_serializer = TeamSerializer(team)
        logger.info(f"User {user.username} removed from team {team.name} by {request.user.username}")
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    

class TaskCreateAPIView(APIView):
    """
    API View to create tasks associated with a specific team.
    """
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = TaskSerializer

    @extend_schema(
        request=TaskSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskSerializer,
                description='Successful Task Creation'
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description='Failed Task Creation'
            )
        }
    )
    def post(self, request, format=None):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            try:
                team = serializer.validated_data['team']
            except Team.DoesNotExist as e:
                return Response({'non_field_errors': [str(e)]}, status=status.HTTP_404_NOT_FOUND)

            self.check_object_permissions(request, team)

            serializer.save(team=team)
            logger.info(f"Task created by {request.user.username} in team {team.name}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"Failed to create task by {request.user.username} in team: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TaskListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskSerializer(many=True),
                description='Successful Task List Fetch'
            ),
            400: OpenApiResponse(
                response=CustomErrorSerializer,
                description='Failed Task List Fetch'
            )
        }
    )
    def get(self, request, format=None):
        try:
            tasks = Task.objects.filter(assigned_to=request.user)
            serializer = TaskSerializer(tasks, many=True)
            logger.info(f"Tasks list fetched by {request.user.username}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(f"Failed to fetch tasks list by {request.user.username}: {str(e)}")
            return Response({'non_field_errors': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)