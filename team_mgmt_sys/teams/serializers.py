from rest_framework import serializers
from teams.models import Team, Task
from django.contrib.auth.models import User

from teams.utils import calculate_completion_rate


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

    def validate(self, data):
        username = data.get("username")
        team = self.context.get("team")

        if not team:
            raise serializers.ValidationError(
                {"non_field_errors": ["Team context is missing."]}
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": ["User Not Found"]})

        if user in team.members.all() or user == team.created_by:
            raise serializers.ValidationError(
                {"non_field_errors": ["User Already in Team"]}
            )

        return data

    def save(self):
        username = self.validated_data.get("username")
        team = self.context.get("team")

        if not team:
            raise ValueError("Team context is missing.")

        user = User.objects.get(username=username)
        team.members.add(user)
        team.save()

        return username


class RemoveMemberSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        team = self.context.get("team")

        if not team:
            raise serializers.ValidationError(
                {"non_field_errors": ["Team context is missing."]}
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": ["User Not Found"]})

        if user == team.created_by:
            raise serializers.ValidationError(
                {"non_field_errors": ["Cannot remove team creator"]}
            )

        if user not in team.members.all():
            raise serializers.ValidationError(
                {"non_field_errors": ["User Not in Team"]}
            )

        return data

    def save(self):
        username = self.validated_data.get("username")
        team = self.context.get("team")

        if not team:
            raise ValueError("Team context is missing.")

        user = User.objects.get(username=username)
        team.members.remove(user)
        team.save()

        # Remove all tasks assigned to the removing user
        tasks = Task.objects.filter(assigned_to=user, team=team)
        for task in tasks:
            task.assigned_to = None
            task.save()

        return username


class TaskDetailSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), allow_null=False, required=True
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "completed",
            "team",
            "assigned_to",
            "due_date",
        )

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

    def update(self, instance, validated_data):
        instance.assigned_to = validated_data.get("assigned_to", instance.assigned_to)
        instance.save()
        return instance


class TaskListResponseSerializer(serializers.Serializer):
    completed_task = TaskDetailSerializer(many=True)
    incomplete_task = TaskDetailSerializer(many=True)
    task_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    def to_representation(self):
        user = self.context.get("user")
        tasks = self.context.get("tasks")

        if user is None:
            raise ValueError("User context is missing.")

        if tasks is None:
            tasks = Task.objects.filter(assigned_to=user)

        completed_tasks = tasks.filter(completed=True).order_by("-due_date")
        incomplete_tasks = tasks.filter(completed=False).order_by("due_date")

        completed_tasks_count = completed_tasks.count()
        incomplete_tasks_count = incomplete_tasks.count()
        total_tasks = completed_tasks_count + incomplete_tasks_count
        if total_tasks == 0:
            completion_rate = 0
        else:
            completion_rate = calculate_completion_rate(
                completed_tasks.count(), total_tasks
            )

        # Serialize tasks
        completed_serializer = TaskDetailSerializer(completed_tasks, many=True)
        incomplete_serializer = TaskDetailSerializer(incomplete_tasks, many=True)

        # Prepare the data
        return {
            "completed_task": completed_serializer.data,
            "incomplete_task": incomplete_serializer.data,
            "task_completion_rate": completion_rate,
        }


class TaskStatusUpdateSerializer(serializers.Serializer):
    completed = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.completed = validated_data.get("completed", instance.completed)
        instance.save()
        return instance


class CustomErrorSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(child=serializers.CharField())
