from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Department, DoctorProfile
from content.serializers import (
    DepartmentDetailSerializer,
    DepartmentPortalSerializer,
    DoctorPortalCardSerializer,
    DoctorPortalDetailSerializer,
)
from content.throttles import PortalAnonThrottle


class PortalDepartmentListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request):
        qs = Department.objects.filter(is_published=True).order_by("display_order", "name")
        limit = request.query_params.get("limit")
        if limit:
            try:
                qs = qs[: max(0, int(limit))]
            except ValueError:
                return Response(
                    {"error": {"code": "invalid_limit", "message": "limit must be integer"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(DepartmentPortalSerializer(qs, many=True).data)


class PortalDepartmentDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request, slug: str):
        try:
            dept = Department.objects.get(slug=slug, is_published=True)
        except Department.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "department not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        doctor_profiles = (
            DoctorProfile.objects.filter(
                is_published=True,
                department_links__department_id=dept.id,
            )
            .select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
            .distinct()
        )
        return Response(
            {
                "department": DepartmentDetailSerializer(dept).data,
                "doctors": DoctorPortalCardSerializer(doctor_profiles, many=True).data,
            }
        )


class PortalDoctorListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request):
        qs = (
            DoctorProfile.objects.filter(is_published=True)
            .select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
        )
        slug = request.query_params.get("department")
        if slug:
            qs = qs.filter(department_links__department__slug=slug).distinct()
        return Response(DoctorPortalCardSerializer(qs, many=True).data)


class PortalDoctorDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request, user_id: int):
        try:
            profile = (
                DoctorProfile.objects.select_related("user")
                .prefetch_related("department_links__department")
                .get(user_id=user_id, is_published=True)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "doctor not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DoctorPortalDetailSerializer(profile).data)
