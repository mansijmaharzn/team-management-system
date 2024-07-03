from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q

from teams.serializers import TeamSerializer
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