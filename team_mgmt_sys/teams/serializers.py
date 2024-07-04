from rest_framework import serializers
from teams.models import Team, Task
from django.contrib.auth.models import User


class TeamSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    members = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'created_at', 'created_by', 'members')


class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()


class RemoveMemberSerializer(serializers.Serializer):
    username = serializers.CharField()


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'completed', 'team', 'assigned_to')