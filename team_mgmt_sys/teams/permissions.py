from rest_framework import permissions


class IsTeamCreator(permissions.BasePermission):
    """
    Custom permission to only allow the creator of the team to modify it.
    """

    def has_object_permission(self, request, view, obj):
        print("permission")
        # Allow GET, HEAD or OPTIONS requests (read-only permissions).
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the requesting user is the creator of the team
        return obj.created_by == request.user