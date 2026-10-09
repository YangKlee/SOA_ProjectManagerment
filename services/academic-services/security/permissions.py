from rest_framework.permissions import BasePermission, SAFE_METHODS


class ReadOnlyOrRoleOneWrite(BasePermission):
    """Allow every authenticated role to read; role 1 is required to write."""

    message = "Only users with role 1 may modify academic data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.auth is not None and request.auth.get("role") == 1
