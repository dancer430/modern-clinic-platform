"""Appointments domain services.

Each function here is the single place where the corresponding workflow
mutates state. Views deserialize input, call into the service, and serialize
the returned model. Role authorization, state-machine guards, and slot
availability checks all live here so the business rules are not scattered
across serializers and view bodies.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as date_type
from datetime import time as time_type

from django.db import transaction

from common.errors import DomainError, PermissionDeniedError
from users.models import User

from .models import Appointment, AppointmentAttachment, DoctorScheduleSlot
from .state import assert_transition


@dataclass(frozen=True)
class AttachmentInput:
    file_name: str
    image_data: str
    image_type: str = "image/jpeg"
    compressed_size: int = 0


def _is_responsible_doctor_or_admin(actor: User, appointment: Appointment) -> bool:
    return actor.role == User.Role.ADMIN or (
        actor.role == User.Role.DOCTOR and appointment.doctor_id == actor.id
    )


def assert_can_create(actor: User, *, patient: User, doctor: User) -> None:
    if doctor.role != User.Role.DOCTOR:
        raise DomainError("doctor must be a doctor role user")
    if patient.role != User.Role.PATIENT:
        raise DomainError("patient must be a patient role user")
    if actor.role == User.Role.PATIENT and patient.id != actor.id:
        raise PermissionDeniedError("patient can only create own appointment")


def assert_can_operate(actor: User, appointment: Appointment, *, message: str) -> None:
    if not _is_responsible_doctor_or_admin(actor, appointment):
        raise PermissionDeniedError(message)


def assert_can_cancel(actor: User, appointment: Appointment) -> None:
    if actor.role == User.Role.ADMIN:
        return
    if appointment.patient_id == actor.id or appointment.doctor_id == actor.id:
        return
    raise PermissionDeniedError("only related user or admin can cancel")


def is_slot_blocked(*, doctor: User, slot_date: date_type, slot_time: time_type) -> bool:
    return DoctorScheduleSlot._default_manager.filter(
        doctor=doctor,
        slot_date=slot_date,
        slot_time=slot_time,
        is_available=False,
    ).exists()


@transaction.atomic
def create_appointment(
    *,
    actor: User,
    patient: User,
    doctor: User,
    appointment_date: date_type,
    appointment_time: time_type,
    reason: str,
) -> Appointment:
    assert_can_create(actor, patient=patient, doctor=doctor)
    if is_slot_blocked(doctor=doctor, slot_date=appointment_date, slot_time=appointment_time):
        raise DomainError("selected slot is unavailable by doctor schedule")
    appointment = Appointment._default_manager.create(
        patient=patient,
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=reason,
        created_by=actor,
    )
    return appointment


@transaction.atomic
def confirm_appointment(*, actor: User, appointment: Appointment, confirm_info: str) -> Appointment:
    assert_can_operate(actor, appointment, message="only responsible doctor or admin can confirm")
    assert_transition(appointment.status, Appointment.Status.CONFIRMED)
    appointment.status = Appointment.Status.CONFIRMED
    appointment.confirm_info = confirm_info
    appointment.save(update_fields=["status", "confirm_info", "updated_at"])
    return appointment


@transaction.atomic
def complete_appointment(
    *,
    actor: User,
    appointment: Appointment,
    diagnosis_result: str,
    treatment_plan: str,
    medical_advice: str = "",
    attachments: Iterable[AttachmentInput] = (),
) -> Appointment:
    assert_can_operate(actor, appointment, message="only responsible doctor or admin can complete")
    assert_transition(appointment.status, Appointment.Status.COMPLETED)
    appointment.status = Appointment.Status.COMPLETED
    appointment.diagnosis_result = diagnosis_result
    appointment.treatment_plan = treatment_plan
    appointment.medical_advice = medical_advice
    appointment.save(
        update_fields=[
            "status",
            "diagnosis_result",
            "treatment_plan",
            "medical_advice",
            "updated_at",
        ]
    )
    attach_completion_attachments(appointment=appointment, items=attachments, uploader=actor)
    return appointment


@transaction.atomic
def cancel_appointment(*, actor: User, appointment: Appointment) -> Appointment:
    assert_can_cancel(actor, appointment)
    assert_transition(appointment.status, Appointment.Status.CANCELLED)
    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=["status", "updated_at"])
    return appointment


def attach_completion_attachments(
    *,
    appointment: Appointment,
    items: Iterable[AttachmentInput],
    uploader: User | None,
) -> list[AppointmentAttachment]:
    rows = list(items)
    if not rows:
        return []
    return AppointmentAttachment._default_manager.bulk_create(
        [
            AppointmentAttachment(
                appointment=appointment,
                file_name=item.file_name,
                image_data=item.image_data,
                image_type=item.image_type or "image/jpeg",
                compressed_size=item.compressed_size or 0,
                uploaded_by=uploader,
            )
            for item in rows
        ]
    )
