from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import DoctorProfile
from content.permissions import IsDoctorUser
from content.serializers import DoctorProfileSelfSerializer
from content.services import DraftConflictError, save_doctor_draft, submit_doctor_review


def _get_or_create(user) -> DoctorProfile:
    profile, _ = DoctorProfile.objects.get_or_create(user=user)
    return profile


class DoctorProfileMeView(APIView):
    permission_classes = (IsDoctorUser,)

    def get(self, request):
        profile = _get_or_create(request.user)
        return Response(DoctorProfileSelfSerializer(profile).data)

    def put(self, request):
        profile = _get_or_create(request.user)
        ser = DoctorProfileSelfSerializer(instance=profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            save_doctor_draft(profile, fields=dict(ser.validated_data))
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileSelfSerializer(profile).data)


class DoctorSubmitReviewView(APIView):
    permission_classes = (IsDoctorUser,)

    def post(self, request):
        profile = _get_or_create(request.user)
        try:
            submit_doctor_review(profile)
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileSelfSerializer(profile).data)
