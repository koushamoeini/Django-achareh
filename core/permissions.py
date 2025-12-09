from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit an object."""

    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the object
        return getattr(obj, 'creator', None) == request.user or getattr(obj, 'contractor', None) == request.user
