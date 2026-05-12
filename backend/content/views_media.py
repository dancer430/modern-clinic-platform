from __future__ import annotations

import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
EXT_BY_CONTENT_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}
DEFAULT_MAX_BYTES = 5 * 1024 * 1024


class IsAdminOrDoctor(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role in (User.Role.ADMIN, User.Role.DOCTOR))


class MediaUploadView(APIView):
    permission_classes = (IsAdminOrDoctor,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"error": {"code": "no_file", "message": "file field is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            return Response(
                {"error": {"code": "invalid_type", "message": "only PNG/JPG/WEBP allowed"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        max_bytes = getattr(settings, "MEDIA_UPLOAD_MAX_BYTES", DEFAULT_MAX_BYTES)
        if upload.size > max_bytes:
            return Response(
                {"error": {"code": "too_large", "message": f"max {max_bytes} bytes"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = EXT_BY_CONTENT_TYPE[upload.content_type]
        key = f"inline/{uuid.uuid4().hex}.{ext}"
        saved_path = default_storage.save(key, upload)
        url = default_storage.url(saved_path)
        return Response({"url": url}, status=status.HTTP_201_CREATED)
