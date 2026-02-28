from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import connection
from django.contrib.auth.password_validation import validate_password

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
            "first_name",
            "last_name",
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
                User._default_manager.filter(email__iexact=identifier)
                .order_by("id")
                .first()
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


class UserManageSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    user_type = serializers.CharField(source="role", read_only=True)
    password = serializers.CharField(required=False, write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "user_type",
            "phone",
            "avatar_data",
            "avatar_type",
            "avatar_size",
            "is_active",
            "password",
        ]

    def validate(self, attrs):
        role_value = self.context.get("role_value") or getattr(
            self.instance, "role", ""
        )
        editing_id = getattr(self.instance, "id", None)

        for field in ["username", "first_name", "last_name", "email", "phone"]:
            value = attrs.get(field)
            if isinstance(value, str):
                attrs[field] = value.strip()

        current_username = attrs.get("username")
        current_first_name = attrs.get("first_name")
        current_last_name = attrs.get("last_name")
        current_email = attrs.get("email")
        current_phone = attrs.get("phone")

        if self.instance is not None:
            current_username = current_username or self.instance.username
            current_first_name = current_first_name or self.instance.first_name
            current_last_name = current_last_name or self.instance.last_name
            current_email = (
                current_email if current_email is not None else self.instance.email
            )
            current_phone = (
                current_phone if current_phone is not None else self.instance.phone
            )

        if not current_username:
            raise serializers.ValidationError({"username": "username is required"})
        if not current_first_name:
            raise serializers.ValidationError({"first_name": "first name is required"})
        if not current_last_name:
            raise serializers.ValidationError({"last_name": "last name is required"})

        users_qs = User._default_manager.all()
        if editing_id is not None:
            users_qs = users_qs.exclude(id=editing_id)

        if current_email:
            if users_qs.filter(email__iexact=current_email).exists():
                raise serializers.ValidationError({"email": "email already exists"})

        if role_value == User.Role.DOCTOR:
            if not current_email:
                raise serializers.ValidationError(
                    {"email": "email is required for doctor"}
                )
            if not current_phone:
                raise serializers.ValidationError(
                    {"phone": "phone is required for doctor"}
                )
            if users_qs.filter(phone=current_phone).exists():
                raise serializers.ValidationError({"phone": "phone already exists"})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", "123456")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
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

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("current password is incorrect")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                "new password and confirm password do not match"
            )
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs


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
            raise serializers.ValidationError(
                {"platform_name": "platform name is required"}
            )

        logo_data = next_attrs.get("logo_data")
        logo_type = next_attrs.get("logo_type", "")
        logo_size = next_attrs.get("logo_size")

        if logo_data:
            if not logo_data.startswith("data:image/"):
                raise serializers.ValidationError(
                    {"logo_data": "logo_data must be image data URL"}
                )
            if logo_type not in ["image/png", "image/jpeg", "image/jpg"]:
                raise serializers.ValidationError(
                    {"logo_type": "logo_type must be png/jpg/jpeg"}
                )
            if logo_size is None or logo_size > 1024:
                raise serializers.ValidationError(
                    {"logo_size": "logo size must be <= 1MB"}
                )

        return next_attrs
