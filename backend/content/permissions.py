from __future__ import annotations

from rest_framework.permissions import BasePermission

from users.models import User


class IsAdminUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN
        )


class IsDoctorUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.DOCTOR
        )
