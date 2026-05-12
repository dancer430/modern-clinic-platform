from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Department, DoctorProfile
from content.permissions import IsAdminUser
from content.serializers import (
    DepartmentAdminSerializer,
    DoctorAssignmentItemSerializer,
    DoctorProfileAdminSerializer,
    RejectNoteSerializer,
)
from content.services import (
    DraftConflictError,
    approve_doctor_profile,
    reject_doctor_profile,
    set_doctor_departments,
)


class AdminDepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("display_order", "name")
    serializer_class = DepartmentAdminSerializer
    permission_classes = (IsAdminUser,)


class AdminDoctorProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorProfileAdminSerializer
    permission_classes = (IsAdminUser,)
    lookup_field = "user_id"
    http_method_names = ("get", "put", "patch", "head", "options")

    def get_queryset(self):
        return (
            DoctorProfile.objects.select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
        )


class AdminDoctorDepartmentsView(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request, user_id: int):
        ser = DoctorAssignmentItemSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        try:
            profile = DoctorProfile.objects.get(user_id=user_id)
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "doctor profile not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            set_doctor_departments(profile, assignments=ser.validated_data)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_assignment", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminApproveDoctorView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, user_id: int):
        profile = _get_profile_or_404(user_id)
        if isinstance(profile, Response):
            return profile
        try:
            approve_doctor_profile(profile)
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminRejectDoctorView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, user_id: int):
        ser = RejectNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = _get_profile_or_404(user_id)
        if isinstance(profile, Response):
            return profile
        try:
            reject_doctor_profile(profile, note=ser.validated_data["note"])
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminPendingReviewsView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        qs = (
            DoctorProfile.objects.filter(draft_status=DoctorProfile.DraftStatus.PENDING)
            .select_related("user")
            .order_by("draft_submitted_at")
        )
        return Response(DoctorProfileAdminSerializer(qs, many=True).data)


def _get_profile_or_404(user_id: int):
    try:
        return DoctorProfile.objects.get(user_id=user_id)
    except DoctorProfile.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "doctor profile not found"}},
            status=status.HTTP_404_NOT_FOUND,
        )
