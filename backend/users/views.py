from rest_framework import permissions, serializers, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from typing import Any

from .models import User
from .serializers import (
    LoginTokenSerializer,
    PasswordChangeSerializer,
    PlatformSettingSerializer,
    ProfileUpdateSerializer,
    UserManageSerializer,
    UserSerializer,
)
from .models import PlatformSetting


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
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data: Any = serializer.validated_data
        new_password = (
            validated_data.get("new_password")
            if isinstance(validated_data, dict)
            else None
        )
        if not isinstance(new_password, str):
            return Response({"detail": "invalid new password"}, status=400)
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
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

    @extend_schema(
        request=PlatformSettingSerializer, responses=PlatformSettingSerializer
    )
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
        refresh = None
        if isinstance(request.data, dict):
            refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass
        return Response({"detail": "logged out"})


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
        serializer.save(role=self.role_value)

    def perform_update(self, serializer):
        serializer.save(role=self.role_value)


class DoctorViewSet(BaseRoleUserViewSet):
    role_value = User.Role.DOCTOR

    @extend_schema(responses=UserSerializer(many=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PatientViewSet(BaseRoleUserViewSet):
    role_value = User.Role.PATIENT

    @extend_schema(responses=UserSerializer(many=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
