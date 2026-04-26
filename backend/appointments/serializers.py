from datetime import time

from rest_framework import serializers

from users.models import User

from .models import Appointment, AppointmentAttachment, DoctorScheduleSlot

# 30-minute clinic slots: 08:00-11:30 and 14:00-17:00.
ALLOWED_SLOT_TIMES = {
    time(8, 0),
    time(8, 30),
    time(9, 0),
    time(9, 30),
    time(10, 0),
    time(10, 30),
    time(11, 0),
    time(11, 30),
    time(14, 0),
    time(14, 30),
    time(15, 0),
    time(15, 30),
    time(16, 0),
    time(16, 30),
    time(17, 0),
}


class AppointmentSerializer(serializers.ModelSerializer):
    """Shape-only serializer.

    Role checks, slot-availability checks, and state transitions live in
    appointments.services. The only domain rule kept here is the
    finite set of allowed slot times, a pure shape constraint.
    """

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    def _display_name(self, user):
        return (user.name or "").strip() or user.username

    def get_patient_name(self, obj):
        return self._display_name(obj.patient)

    def get_doctor_name(self, obj):
        return self._display_name(obj.doctor)

    def get_attachments(self, obj):
        return AppointmentAttachmentSerializer(obj.attachments.all(), many=True).data

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "appointment_date",
            "appointment_time",
            "reason",
            "status",
            "confirm_info",
            "diagnosis_result",
            "treatment_plan",
            "medical_advice",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "confirm_info",
            "diagnosis_result",
            "treatment_plan",
            "medical_advice",
            "created_at",
            "updated_at",
        ]

    def validate_appointment_time(self, value):
        if value not in ALLOWED_SLOT_TIMES:
            raise serializers.ValidationError(
                "appointment_time must be in allowed 30-minute clinic slots"
            )
        return value


class AppointmentConfirmSerializer(serializers.Serializer):
    confirm_info = serializers.CharField(max_length=500)


class AppointmentCompleteSerializer(serializers.Serializer):
    class AttachmentInputSerializer(serializers.Serializer):
        file_name = serializers.CharField(max_length=255)
        image_data = serializers.CharField()
        image_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
        compressed_size = serializers.IntegerField(required=False, min_value=0)

    diagnosis_result = serializers.CharField()
    treatment_plan = serializers.CharField()
    medical_advice = serializers.CharField(required=False, allow_blank=True)
    attachments = AttachmentInputSerializer(many=True, required=False)

    def validate_attachments(self, value):
        for item in value:
            if not item["image_data"].startswith("data:image/"):
                raise serializers.ValidationError("attachment image_data must be image data URL")
        return value


class AppointmentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class AppointmentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentAttachment
        fields = [
            "id",
            "file_name",
            "image_data",
            "image_type",
            "compressed_size",
            "created_at",
        ]


class ScheduleSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.username", read_only=True)

    class Meta:
        model = DoctorScheduleSlot
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "slot_date",
            "slot_time",
            "is_available",
            "created_at",
            "updated_at",
        ]

    def validate_slot_time(self, value):
        if value not in ALLOWED_SLOT_TIMES:
            raise serializers.ValidationError("slot_time must be in allowed 30-minute clinic slots")
        return value

    def validate_doctor(self, value):
        if value.role != User.Role.DOCTOR:
            raise serializers.ValidationError("doctor must be a doctor role user")
        return value
