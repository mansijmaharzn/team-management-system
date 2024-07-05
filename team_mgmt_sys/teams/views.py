import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from teams.serializers import TeamSerializer, AddMemberSerializer, RemoveMemberSerializer, TaskSerializer
from teams.permissions import IsTeamCreator
from teams.models import Team, Task


logger = logging.getLogger(__name__)


class TeamCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

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

    def get(self, request, format=None):
        teams = Team.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
        serializer = TeamSerializer(teams, many=True)
        logger.info(f"Teams list fetched by {request.user.username}")
        return Response(serializer.data)
    

class AddMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = AddMemberSerializer

    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        user = get_object_or_404(User, username=username)

        if user in team.members.all() or user == team.created_by:
            return Response({'detail': 'User is already a member of the team.'}, status=status.HTTP_400_BAD_REQUEST)
        
        team.members.add(user)
        team.save()

        serializer = TeamSerializer(team)
        logger.info(f"User {user.username} added to team {team.name} by {request.user.username}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RemoveMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = RemoveMemberSerializer

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

    def post(self, request, team_id, format=None):
        team = get_object_or_404(Team, pk=team_id)
        self.check_object_permissions(request, team)

        data = request.data
        data['team'] = team.id
        serializer = TaskSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"Task created by {request.user.username} in team {team.name}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        logger.warning(f"Failed to create task by {request.user.username} in team {team.name}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TaskListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get(self, request, format=None):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = TaskSerializer(tasks, many=True)
        logger.info(f"Tasks list fetched by {request.user.username}")
        return Response(serializer.data, status=status.HTTP_200_OK)