from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"
        OPERATOR = "operator", "Operations"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_data = models.TextField(blank=True)
    avatar_type = models.CharField(max_length=50, blank=True)
    avatar_size = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.username


class PlatformSetting(models.Model):
    platform_name = models.CharField(max_length=120, default="Medical Booking Platform")
    logo_data = models.TextField(blank=True)
    logo_type = models.CharField(max_length=50, blank=True)
    logo_size = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.platform_name
