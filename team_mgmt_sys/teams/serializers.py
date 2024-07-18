from rest_framework import serializers
from teams.models import Team, Task
from django.contrib.auth.models import User


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "created_by")


class TeamDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source="created_by.username")
    members = serializers.SlugRelatedField(
        many=True, slug_field="username", queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Team
        fields = ("id", "name", "description", "created_at", "created_by", "members")


class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()


class RemoveMemberSerializer(serializers.Serializer):
    username = serializers.CharField()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "completed", "assigned_to")


class TaskDetailSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), allow_null=False, required=True
    )

    class Meta:
        model = Task
        fields = ("id", "title", "description", "completed", "team", "assigned_to")

    def validate(self, data):
        team = data.get("team")
        assigned_to = data.get("assigned_to")

        if (
            assigned_to
            and assigned_to not in team.members.all()
            and assigned_to != team.created_by
        ):
            raise serializers.ValidationError(
                "Assigned user must be a team member or the team creator."
            )

        return data


class TaskAssignedUserUpdateSerializer(serializers.Serializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Task
        fields = ("assigned_to",)

    def validate_assigned_to(self, value):
        task = self.instance  # instance is the task object
        if value not in task.team.members.all() and value != task.team.created_by:
            raise serializers.ValidationError(
                "Assigned user must be a team member or the team creator."
            )
        return value


class TaskListResponseSerializer(serializers.Serializer):
    completed_task = TaskDetailSerializer(many=True)
    incomplete_task = TaskDetailSerializer(many=True)


class TaskStatusUpdateSerializer(serializers.Serializer):
    completed = serializers.BooleanField()


class CustomErrorSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(child=serializers.CharField())
