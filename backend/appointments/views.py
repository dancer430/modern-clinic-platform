from django.db import connection
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from users.models import User

from .models import Appointment, AppointmentAttachment, DoctorScheduleSlot
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
        status_param = self.request.query_params.get("status")
        doctor_param = self.request.query_params.get("doctor")
        patient_param = self.request.query_params.get("patient")
        date_param = self.request.query_params.get("date")
        date_from_param = self.request.query_params.get("date_from")
        date_to_param = self.request.query_params.get("date_to")
        query_param = self.request.query_params.get("q")

        if status_param:
            queryset = queryset.filter(status=status_param)
        if doctor_param:
            queryset = queryset.filter(doctor_id=doctor_param)
        if patient_param:
            queryset = queryset.filter(patient_id=patient_param)
        if date_param:
            queryset = queryset.filter(appointment_date=date_param)
        if date_from_param:
            queryset = queryset.filter(appointment_date__gte=date_from_param)
        if date_to_param:
            queryset = queryset.filter(appointment_date__lte=date_to_param)
        if query_param:
            q = query_param.strip()
            if q:
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
        user = self.request.user
        patient = serializer.validated_data["patient"]

        if user.role == User.Role.PATIENT and patient != user:
            raise PermissionDenied("patient can only create own appointment")

        serializer.save(created_by=user)

    def _can_doctor_operate(self, appointment):
        user = self.request.user
        return user.role == User.Role.ADMIN or (
            user.role == User.Role.DOCTOR and appointment.doctor_id == user.id
        )

    @action(detail=True, methods=["put"], url_path="confirm")
    def confirm(self, request, pk: int | None = None):
        appointment = self.get_object()
        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {"detail": "only pending appointment can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self._can_doctor_operate(appointment):
            raise PermissionDenied("only responsible doctor or admin can confirm")

        serializer = AppointmentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.status = Appointment.Status.CONFIRMED
        appointment.confirm_info = serializer.validated_data["confirm_info"]
        appointment.save(update_fields=["status", "confirm_info", "updated_at"])
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["put"], url_path="complete")
    def complete(self, request, pk: int | None = None):
        appointment = self.get_object()
        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {"detail": "only confirmed appointment can be completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self._can_doctor_operate(appointment):
            raise PermissionDenied("only responsible doctor or admin can complete")

        serializer = AppointmentCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = serializer.validated_data.get("attachments", [])

        if attachments and connection.vendor != "postgresql":
            return Response(
                {"detail": "attachments are only supported when database is PostgreSQL"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.COMPLETED
        appointment.diagnosis_result = serializer.validated_data["diagnosis_result"]
        appointment.treatment_plan = serializer.validated_data["treatment_plan"]
        appointment.medical_advice = serializer.validated_data.get("medical_advice", "")
        appointment.save(
            update_fields=[
                "status",
                "diagnosis_result",
                "treatment_plan",
                "medical_advice",
                "updated_at",
            ]
        )

        if attachments:
            AppointmentAttachment._default_manager.bulk_create(
                [
                    AppointmentAttachment(
                        appointment=appointment,
                        file_name=item["file_name"],
                        image_data=item["image_data"],
                        image_type=item.get("image_type") or "image/jpeg",
                        compressed_size=item.get("compressed_size", 0),
                        uploaded_by=request.user,
                    )
                    for item in attachments
                ]
            )

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["put"], url_path="cancel")
    def cancel(self, request, pk: int | None = None):
        appointment = self.get_object()
        if appointment.status not in [
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
        ]:
            return Response(
                {"detail": "only pending/confirmed appointment can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        is_related = appointment.patient_id == user.id or appointment.doctor_id == user.id
        if user.role != User.Role.ADMIN and not is_related:
            raise PermissionDenied("only related user or admin can cancel")

        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])
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

    def perform_create(self, serializer):
        user = self.request.user
        doctor = serializer.validated_data["doctor"]
        if user.role == User.Role.ADMIN:
            serializer.save()
            return
        if user.role == User.Role.DOCTOR and doctor.id == user.id:
            serializer.save()
            return
        raise PermissionDenied("only admin or owner doctor can create schedule slot")

    def perform_update(self, serializer):
        user = self.request.user
        doctor = serializer.instance.doctor
        target_doctor = serializer.validated_data.get("doctor", doctor)
        if user.role == User.Role.ADMIN or (
            user.role == User.Role.DOCTOR and doctor.id == user.id and target_doctor.id == user.id
        ):
            serializer.save()
            return
        raise PermissionDenied("only admin or owner doctor can update schedule slot")

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role == User.Role.ADMIN or (
            user.role == User.Role.DOCTOR and instance.doctor_id == user.id
        ):
            instance.delete()
            return
        raise PermissionDenied("only admin or owner doctor can delete schedule slot")
