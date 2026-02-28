from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, ScheduleSlotViewSet

router = DefaultRouter()
router.register("appointments", AppointmentViewSet, basename="appointments")
router.register("schedule-slots", ScheduleSlotViewSet, basename="schedule-slots")

urlpatterns = [
    path("", include(router.urls)),
]
