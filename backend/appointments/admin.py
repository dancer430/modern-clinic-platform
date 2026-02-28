from django.contrib import admin

from .models import Appointment, AppointmentAttachment, DoctorScheduleSlot


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
        "created_at",
    )
    list_filter = ("status", "appointment_date")
    search_fields = ("patient__username", "doctor__username")


@admin.register(DoctorScheduleSlot)
class DoctorScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "slot_date", "slot_time", "is_available")
    list_filter = ("is_available", "slot_date")
    search_fields = ("doctor__username",)


@admin.register(AppointmentAttachment)
class AppointmentAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "file_name",
        "image_type",
        "compressed_size",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("image_type", "created_at")
    search_fields = ("appointment__id", "file_name", "uploaded_by__username")
