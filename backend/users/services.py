"""User-management domain services.

Owns role-aware user creation, username uniqueness + suggestion, password
change, and refresh-token logout. Serializers in this app shrink to shape
validation only; uniqueness checks and the ``next-available-suffix``
suggestion path are reachable here because the serializer no longer
auto-validates uniqueness via DRF's ``UniqueValidator``.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.db import transaction
from rest_framework import serializers as drf_serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.errors import ConflictError, DomainError

from .models import User


def suggest_username(base: str, *, exclude_id: int | None = None) -> str:
    base = base.strip()
    if not base:
        return ""
    qs = User._default_manager.all()
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    taken = {
        u.lower()
        for u in qs.filter(username__iregex=rf"^{base}\d*$").values_list("username", flat=True)
    }
    suffix = 2
    while f"{base}{suffix}".lower() in taken:
        suffix += 1
    return f"{base}{suffix}"


def assert_unique_username(username: str, *, exclude_id: int | None = None) -> None:
    qs = User._default_manager.filter(username__iexact=username)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        suggestion = suggest_username(username, exclude_id=exclude_id)
        raise drf_serializers.ValidationError(
            {"username": [f"username already exists, please try '{suggestion}'"]}
        )


def assert_unique_email(email: str, *, exclude_id: int | None = None) -> None:
    if not email:
        return
    qs = User._default_manager.filter(email__iexact=email)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise drf_serializers.ValidationError({"email": ["email already exists"]})


def assert_doctor_fields(*, email: str, phone: str, exclude_id: int | None = None) -> None:
    if not email:
        raise drf_serializers.ValidationError({"email": ["email is required for doctor"]})
    if not phone:
        raise drf_serializers.ValidationError({"phone": ["phone is required for doctor"]})
    qs = User._default_manager.filter(phone=phone)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise drf_serializers.ValidationError({"phone": ["phone already exists"]})


@transaction.atomic
def create_user_with_role(*, role: str, attrs: dict[str, Any]) -> User:
    username = (attrs.get("username") or "").strip()
    email = (attrs.get("email") or "").strip()
    phone = (attrs.get("phone") or "").strip()
    name = (attrs.get("name") or "").strip()

    if not username:
        raise drf_serializers.ValidationError({"username": ["username is required"]})
    if not name:
        raise drf_serializers.ValidationError({"name": ["name is required"]})

    assert_unique_username(username)
    assert_unique_email(email)
    if role == User.Role.DOCTOR:
        assert_doctor_fields(email=email, phone=phone)

    password = attrs.pop("password", None) or "123456"
    user = User(
        username=username,
        email=email,
        phone=phone,
        name=name,
        role=role,
        avatar_data=attrs.get("avatar_data") or "",
        avatar_type=attrs.get("avatar_type") or "",
        avatar_size=attrs.get("avatar_size"),
        is_active=attrs.get("is_active", True),
    )
    user.set_password(password)
    user.save()
    return user


@transaction.atomic
def update_user_with_role(*, user: User, role: str, attrs: dict[str, Any]) -> User:
    username = attrs.get("username", user.username).strip()
    email = (attrs.get("email", user.email) or "").strip()
    phone = (attrs.get("phone", user.phone) or "").strip()
    name = attrs.get("name", user.name).strip()

    if not username:
        raise drf_serializers.ValidationError({"username": ["username is required"]})
    if not name:
        raise drf_serializers.ValidationError({"name": ["name is required"]})

    assert_unique_username(username, exclude_id=user.id)
    assert_unique_email(email, exclude_id=user.id)
    if role == User.Role.DOCTOR:
        assert_doctor_fields(email=email, phone=phone, exclude_id=user.id)

    user.username = username
    user.email = email
    user.phone = phone
    user.name = name
    if "avatar_data" in attrs:
        user.avatar_data = attrs["avatar_data"] or ""
    if "avatar_type" in attrs:
        user.avatar_type = attrs["avatar_type"] or ""
    if "avatar_size" in attrs:
        user.avatar_size = attrs["avatar_size"]
    if "is_active" in attrs:
        user.is_active = attrs["is_active"]

    if password := attrs.get("password"):
        user.set_password(password)
    user.save()
    return user


def change_password(
    *, user: User, current_password: str, new_password: str, confirm_password: str
) -> None:
    if not user.check_password(current_password):
        raise drf_serializers.ValidationError(
            {"current_password": ["current password is incorrect"]}
        )
    if new_password != confirm_password:
        raise drf_serializers.ValidationError("new password and confirm password do not match")
    django_validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password"])


def logout(refresh_token: str | None) -> None:
    if not refresh_token:
        return
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as exc:
        raise ConflictError("refresh token is invalid or already blacklisted") from exc
    except Exception as exc:  # safety net for unexpected SimpleJWT internals
        raise DomainError(f"logout failed: {exc}") from exc
