from typing import Any

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .models import PlatformSetting, User
from .serializers import (
    LoginTokenSerializer,
    PasswordChangeSerializer,
    PlatformSettingSerializer,
    ProfileUpdateSerializer,
    UserManageSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginTokenSerializer


class MeView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    @extend_schema(request=PasswordChangeSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        validated: Any = serializer.validated_data
        services.change_password(
            user=request.user,
            current_password=validated["current_password"],
            new_password=validated["new_password"],
            confirm_password=validated["confirm_password"],
        )
        return Response({"detail": "password updated"})


class PlatformSettingView(GenericAPIView):
    serializer_class = PlatformSettingSerializer

    def get_permissions(self):
        if self.request.method.upper() == "PATCH":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def _get_setting(self):
        setting = PlatformSetting._default_manager.order_by("id").first()
        if setting is None:
            setting = PlatformSetting._default_manager.create()
        return setting

    @extend_schema(responses=PlatformSettingSerializer)
    def get(self, request):
        setting = self._get_setting()
        return Response(PlatformSettingSerializer(setting).data)

    @extend_schema(request=PlatformSettingSerializer, responses=PlatformSettingSerializer)
    def patch(self, request):
        setting = self._get_setting()
        serializer = PlatformSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PlatformSettingSerializer(setting).data)


class LogoutView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        request=inline_serializer(
            name="LogoutRequest",
            fields={"refresh": serializers.CharField(required=False, allow_blank=True)},
        ),
        responses={200: None},
    )
    def post(self, request):
        refresh = request.data.get("refresh") if isinstance(request.data, dict) else None
        services.logout(refresh)
        return Response({"detail": "logged out"})


class CanCreatePatientPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(
            user.is_superuser
            or user.is_staff
            or getattr(user, "role", "") in [User.Role.ADMIN, User.Role.DOCTOR]
        )


class BaseRoleUserViewSet(viewsets.ModelViewSet):
    queryset = User._default_manager.none()
    serializer_class = UserManageSerializer
    permission_classes = [permissions.IsAuthenticated]
    role_value = ""

    def get_queryset(self):
        return User._default_manager.filter(role=self.role_value).order_by("id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["role_value"] = self.role_value
        return context

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = services.create_user_with_role(
            role=self.role_value,
            attrs=dict(serializer.validated_data),
        )
        serializer.instance = user

    def perform_update(self, serializer):
        user = services.update_user_with_role(
            user=serializer.instance,
            role=self.role_value,
            attrs=dict(serializer.validated_data),
        )
        serializer.instance = user


class DoctorViewSet(BaseRoleUserViewSet):
    role_value = User.Role.DOCTOR

    @extend_schema(responses=UserSerializer(many=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PatientViewSet(BaseRoleUserViewSet):
    role_value = User.Role.PATIENT

    def get_permissions(self):
        if self.action == "create":
            return [CanCreatePatientPermission()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @extend_schema(responses=UserSerializer(many=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
