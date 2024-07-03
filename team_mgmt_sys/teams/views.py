from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from teams.serializers import TeamSerializer, AddMemberSerializer, RemoveMemberSerializer
from teams.permissions import IsTeamCreator
from teams.models import Team


class TeamCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

    def post(self, request, format=None):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

    def get(self, request, format=None):
        teams = Team.objects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)
    

class AddMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = AddMemberSerializer

    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        user = get_object_or_404(User, username=username)

        if user in team.members.all():
            return Response({'detail': 'User is already a member of the team.'}, status=status.HTTP_400_BAD_REQUEST)
        
        team.members.add(user)
        team.save()

        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RemoveMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeamCreator]
    serializer_class = RemoveMemberSerializer

    def post(self, request, pk, format=None):
        team = get_object_or_404(Team, pk=pk)
        serializer = RemoveMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        user = get_object_or_404(User, username=username)

        if user not in team.members.all():
            return Response({'detail': 'User is not a member of the team.'}, status=status.HTTP_400_BAD_REQUEST)
        
        team.members.remove(user)
        team.save()

        response_serializer = TeamSerializer(team)
        return Response(response_serializer.data, status=status.HTTP_200_OK)