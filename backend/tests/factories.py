from __future__ import annotations

import datetime as dt

import factory
from factory.django import DjangoModelFactory

from appointments.models import Appointment, DoctorScheduleSlot
from users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    name = factory.LazyAttribute(lambda obj: obj.username)
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    phone = factory.Sequence(lambda n: f"139{n:08d}")
    role = User.Role.PATIENT
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "test-pass-1234")
        self.save(update_fields=["password"])


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = Appointment

    patient = factory.SubFactory(UserFactory, role=User.Role.PATIENT)
    doctor = factory.SubFactory(UserFactory, role=User.Role.DOCTOR)
    appointment_date = factory.LazyFunction(lambda: dt.date.today() + dt.timedelta(days=1))
    appointment_time = dt.time(9, 0)
    reason = "Routine checkup"
    status = Appointment.Status.PENDING


class DoctorScheduleSlotFactory(DjangoModelFactory):
    class Meta:
        model = DoctorScheduleSlot

    doctor = factory.SubFactory(UserFactory, role=User.Role.DOCTOR)
    slot_date = factory.LazyFunction(lambda: dt.date.today() + dt.timedelta(days=1))
    slot_time = dt.time(9, 0)
    is_available = True
