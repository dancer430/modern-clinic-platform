from __future__ import annotations

from rest_framework import serializers

from content.models import Department, DoctorProfile


def _image_url(field) -> str | None:
    if not field:
        return None
    try:
        return field.url
    except Exception:
        return None


class DepartmentPortalSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ("id", "slug", "name", "summary", "cover_image_url", "display_order")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DepartmentDetailSerializer(DepartmentPortalSerializer):
    class Meta(DepartmentPortalSerializer.Meta):
        fields = DepartmentPortalSerializer.Meta.fields + ("description_html",)


class DepartmentAdminSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = (
            "id",
            "slug",
            "name",
            "summary",
            "description_html",
            "cover_image",
            "cover_image_url",
            "display_order",
            "is_published",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "cover_image_url")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)

    def validate_description_html(self, value):
        from content.services import sanitize_html

        return sanitize_html(value)


class DoctorDepartmentLinkSerializer(serializers.Serializer):
    slug = serializers.CharField(source="department.slug", read_only=True)
    name = serializers.CharField(source="department.name", read_only=True)
    is_primary = serializers.BooleanField()


class DoctorPortalCardSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id")
    name = serializers.CharField(source="user.name")
    title = serializers.CharField()
    specialty = serializers.CharField()
    cover_image_url = serializers.SerializerMethodField()
    departments = DoctorDepartmentLinkSerializer(many=True, source="department_links")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DoctorPortalDetailSerializer(DoctorPortalCardSerializer):
    bio_published_html = serializers.CharField()


class DoctorProfileSelfSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    departments = DoctorDepartmentLinkSerializer(
        many=True, source="department_links", read_only=True
    )

    class Meta:
        model = DoctorProfile
        fields = (
            "title",
            "specialty",
            "bio_published_html",
            "bio_draft_html",
            "cover_image",
            "cover_image_url",
            "is_published",
            "draft_status",
            "draft_submitted_at",
            "draft_reviewed_at",
            "draft_review_note",
            "departments",
        )
        read_only_fields = (
            "bio_published_html",
            "is_published",
            "draft_status",
            "draft_submitted_at",
            "draft_reviewed_at",
            "draft_review_note",
            "departments",
            "cover_image_url",
        )

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DoctorProfileAdminSerializer(DoctorProfileSelfSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta(DoctorProfileSelfSerializer.Meta):
        fields = ("user_id", "username", "name") + DoctorProfileSelfSerializer.Meta.fields


class DoctorAssignmentItemSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=False)


class RejectNoteSerializer(serializers.Serializer):
    note = serializers.CharField(required=True, allow_blank=False, max_length=2000)
