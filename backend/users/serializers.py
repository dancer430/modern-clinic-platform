from django.db import connection
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PlatformSetting, User


class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(source="role", read_only=True)
    db_vendor = serializers.SerializerMethodField()

    def get_db_vendor(self, obj):
        return connection.vendor

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "name",
            "role",
            "user_type",
            "db_vendor",
            "phone",
            "avatar_data",
            "avatar_type",
            "avatar_size",
        ]


class LoginTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_key = self.username_field
        identifier = attrs.get(username_key)
        if isinstance(identifier, str) and "@" in identifier:
            matched_user = (
                User._default_manager.filter(email__iexact=identifier).order_by("id").first()
            )
            if matched_user is not None:
                attrs = {**attrs, username_key: matched_user.get_username()}

        token_data = super().validate(attrs)
        access = token_data.get("access")
        refresh = token_data.get("refresh")
        if not isinstance(access, str) or not isinstance(refresh, str):
            raise serializers.ValidationError("token payload invalid")
        return {
            "access": access,
            "refresh": refresh,
            "user": UserSerializer(self.user).data,
        }


def _drop_unique_validators(field):
    """Strip DRF's auto-generated UniqueValidator from a serializer field.

    DRF's ModelSerializer attaches a UniqueValidator to every model field
    declared with ``unique=True``. We intentionally route uniqueness through
    ``users.services`` so the suggestion path stays reachable; otherwise the
    auto-validator would emit a generic localized message before the service
    has a chance to compute the next-available username.
    """

    field.validators = [v for v in field.validators if not isinstance(v, UniqueValidator)]
    return field


class UserManageSerializer(serializers.ModelSerializer):
    """Shape-only serializer.

    Uniqueness, role-based required fields, and password defaulting all
    live in ``users.services``. The serializer keeps field types and
    write-only-password handling.
    """

    role = serializers.CharField(read_only=True)
    user_type = serializers.CharField(source="role", read_only=True)
    password = serializers.CharField(required=False, write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "name",
            "role",
            "user_type",
            "phone",
            "avatar_data",
            "avatar_type",
            "avatar_size",
            "is_active",
            "password",
        ]

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(field_name, model_field)
        # We disable validators by stripping them after instantiation in
        # ``build_field``; UniqueValidator is added there.
        return field_class, field_kwargs

    def build_field(self, field_name, info, model_class, nested_depth):
        field_class, field_kwargs = super().build_field(field_name, info, model_class, nested_depth)
        if field_name == "username":
            # Push the UniqueValidator into the service layer (see services
            # docstring). DRF still keeps the trim/strip behavior of CharField.
            existing = field_kwargs.get("validators", [])
            field_kwargs["validators"] = [v for v in existing if not isinstance(v, UniqueValidator)]
        return field_class, field_kwargs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "phone",
            "avatar_data",
            "avatar_type",
            "avatar_size",
        ]

    def validate(self, attrs):
        next_attrs = dict(attrs)
        email = next_attrs.get("email")
        if isinstance(email, str):
            next_attrs["email"] = email.strip()

        target_email = next_attrs.get("email")
        if target_email:
            duplicate = (
                User._default_manager.filter(email__iexact=target_email)
                .exclude(id=getattr(self.instance, "id", None))
                .exists()
            )
            if duplicate:
                raise serializers.ValidationError({"email": "email already exists"})

        avatar_data = next_attrs.get("avatar_data")
        avatar_type = next_attrs.get("avatar_type", "")
        avatar_size = next_attrs.get("avatar_size")

        if avatar_data:
            if not avatar_data.startswith("data:image/"):
                raise serializers.ValidationError("avatar_data must be image data URL")
            if avatar_type not in ["image/png", "image/jpeg", "image/jpg"]:
                raise serializers.ValidationError("avatar_type must be png/jpg/jpeg")
            if avatar_size is None or avatar_size > 1024:
                raise serializers.ValidationError("avatar size must be <= 1MB")

        return next_attrs


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


class PlatformSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSetting
        fields = [
            "id",
            "platform_name",
            "logo_data",
            "logo_type",
            "logo_size",
            "updated_at",
        ]

    def validate(self, attrs):
        next_attrs = dict(attrs)
        platform_name = next_attrs.get("platform_name")
        if isinstance(platform_name, str):
            next_attrs["platform_name"] = platform_name.strip()
        if not next_attrs.get("platform_name"):
            raise serializers.ValidationError({"platform_name": "platform name is required"})

        logo_data = next_attrs.get("logo_data")
        logo_type = next_attrs.get("logo_type", "")
        logo_size = next_attrs.get("logo_size")

        if logo_data:
            if not logo_data.startswith("data:image/"):
                raise serializers.ValidationError({"logo_data": "logo_data must be image data URL"})
            if logo_type not in ["image/png", "image/jpeg", "image/jpg"]:
                raise serializers.ValidationError({"logo_type": "logo_type must be png/jpg/jpeg"})
            if logo_size is None or logo_size > 1024:
                raise serializers.ValidationError({"logo_size": "logo size must be <= 1MB"})

        return next_attrs
