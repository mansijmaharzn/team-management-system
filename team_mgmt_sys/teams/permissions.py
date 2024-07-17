from rest_framework import permissions


class IsTeamCreator(permissions.BasePermission):
    """
    Custom permission to only allow the creator of the team to modify it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is the creator of the team
        return obj.created_by == request.user


class IsTeamMemberOrCreator(permissions.BasePermission):
    """
    Custom permission to only allow team members to view the team.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is the member of the team
        return (
            request.user.username in obj.members.all() or obj.created_by == request.user
        )


class IsAssignedToTask(permissions.BasePermission):
    """
    Custom permission to only allow the assigned user to view the task.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is assigned to the task
        return obj.assigned_to == request.user
