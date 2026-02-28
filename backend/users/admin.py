from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PlatformSetting, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = tuple(DjangoUserAdmin.fieldsets) + (
        ("Profile", {"fields": ("role", "phone")}),
    )
    list_display = ("id", "username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "platform_name", "updated_at")
