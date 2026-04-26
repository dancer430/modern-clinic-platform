from django.db import connection
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from common.errors import PermissionDeniedError
from users.models import User

from . import services
from .models import Appointment, DoctorScheduleSlot
from .serializers import (
    AppointmentCancelSerializer,
    AppointmentCompleteSerializer,
    AppointmentConfirmSerializer,
    AppointmentSerializer,
    ScheduleSlotSerializer,
)


class AppointmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment._default_manager.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AppointmentPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment._default_manager.select_related(
            "patient", "doctor"
        ).prefetch_related("attachments")
        params = self.request.query_params

        if status_param := params.get("status"):
            queryset = queryset.filter(status=status_param)
        if doctor_param := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor_param)
        if patient_param := params.get("patient"):
            queryset = queryset.filter(patient_id=patient_param)
        if date_param := params.get("date"):
            queryset = queryset.filter(appointment_date=date_param)
        if date_from_param := params.get("date_from"):
            queryset = queryset.filter(appointment_date__gte=date_from_param)
        if date_to_param := params.get("date_to"):
            queryset = queryset.filter(appointment_date__lte=date_to_param)
        query_param = params.get("q")
        if query_param and (q := query_param.strip()):
            queryset = queryset.filter(
                Q(patient__username__icontains=q)
                | Q(patient__name__icontains=q)
                | Q(doctor__username__icontains=q)
                | Q(doctor__name__icontains=q)
                | Q(reason__icontains=q)
                | Q(diagnosis_result__icontains=q)
            )

        queryset = queryset.order_by("-appointment_date", "-appointment_time", "-id")

        if user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.DOCTOR:
            return queryset.filter(doctor=user)
        return queryset.filter(patient=user)

    def perform_create(self, serializer):
        validated = serializer.validated_data
        appointment = services.create_appointment(
            actor=self.request.user,
            patient=validated["patient"],
            doctor=validated["doctor"],
            appointment_date=validated["appointment_date"],
            appointment_time=validated["appointment_time"],
            reason=validated.get("reason", ""),
        )
        # Repopulate the serializer instance so DRF returns the persisted row.
        serializer.instance = appointment

    @action(detail=True, methods=["put"], url_path="confirm")
    def confirm(self, request, pk: int | None = None):
        appointment = self.get_object()
        payload = AppointmentConfirmSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        appointment = services.confirm_appointment(
            actor=request.user,
            appointment=appointment,
            confirm_info=payload.validated_data["confirm_info"],
        )
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["put"], url_path="complete")
    def complete(self, request, pk: int | None = None):
        appointment = self.get_object()
        payload = AppointmentCompleteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        attachment_inputs = [
            services.AttachmentInput(
                file_name=item["file_name"],
                image_data=item["image_data"],
                image_type=item.get("image_type") or "image/jpeg",
                compressed_size=item.get("compressed_size", 0),
            )
            for item in payload.validated_data.get("attachments", [])
        ]
        if attachment_inputs and connection.vendor != "postgresql":
            return Response(
                {"detail": "attachments are only supported when database is PostgreSQL"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment = services.complete_appointment(
            actor=request.user,
            appointment=appointment,
            diagnosis_result=payload.validated_data["diagnosis_result"],
            treatment_plan=payload.validated_data["treatment_plan"],
            medical_advice=payload.validated_data.get("medical_advice", ""),
            attachments=attachment_inputs,
        )
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["put"], url_path="cancel")
    def cancel(self, request, pk: int | None = None):
        appointment = self.get_object()
        AppointmentCancelSerializer(data=request.data).is_valid(raise_exception=True)
        appointment = services.cancel_appointment(actor=request.user, appointment=appointment)
        return Response(AppointmentSerializer(appointment).data)


class ScheduleSlotViewSet(viewsets.ModelViewSet):
    queryset = DoctorScheduleSlot._default_manager.all()
    serializer_class = ScheduleSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = DoctorScheduleSlot._default_manager.select_related("doctor")
        if user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.DOCTOR:
            return queryset.filter(doctor=user)
        return queryset

    def _assert_can_manage(self, actor, target_doctor_id: int) -> None:
        if actor.role == User.Role.ADMIN:
            return
        if actor.role == User.Role.DOCTOR and target_doctor_id == actor.id:
            return
        raise PermissionDeniedError("only admin or owner doctor can manage schedule slot")

    def perform_create(self, serializer):
        self._assert_can_manage(self.request.user, serializer.validated_data["doctor"].id)
        serializer.save()

    def perform_update(self, serializer):
        target_doctor = serializer.validated_data.get("doctor", serializer.instance.doctor)
        self._assert_can_manage(self.request.user, target_doctor.id)
        if self.request.user.role == User.Role.DOCTOR and target_doctor.id != self.request.user.id:
            raise PermissionDeniedError("doctor cannot reassign slot to another doctor")
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_can_manage(self.request.user, instance.doctor_id)
        instance.delete()
