from rest_framework.permissions import BasePermission


class IsAdminMBAAY(BasePermission):
    """
    Autorise uniquement les administrateurs MBAAY.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsAgronomeMBAAY(BasePermission):
    """
    Autorise uniquement les agronomes MBAAY.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "AGRONOME"
        )