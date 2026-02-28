from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    DoctorViewSet,
    LoginView,
    LogoutView,
    MeView,
    PatientViewSet,
    PlatformSettingView,
)

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctors")
router.register("patients", PatientViewSet, basename="patients")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("platform/", PlatformSettingView.as_view(), name="platform-setting"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("", include(router.urls)),
]
