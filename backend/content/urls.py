from django.urls import include, path
from rest_framework.routers import SimpleRouter

from content.views_admin import (
    AdminApproveDoctorView,
    AdminDepartmentViewSet,
    AdminDoctorDepartmentsView,
    AdminDoctorProfileViewSet,
    AdminPendingReviewsView,
    AdminRejectDoctorView,
)
from content.views_doctor import DoctorProfileMeView, DoctorSubmitReviewView
from content.views_media import MediaUploadView
from content.views_portal import (
    PortalDepartmentDetailView,
    PortalDepartmentListView,
    PortalDoctorDetailView,
    PortalDoctorListView,
)

admin_router = SimpleRouter()
admin_router.register("departments", AdminDepartmentViewSet, basename="admin-department")
admin_router.register("doctor-profiles", AdminDoctorProfileViewSet, basename="admin-doctor-profile")

urlpatterns = [
    path("portal/departments/", PortalDepartmentListView.as_view()),
    path("portal/departments/<slug:slug>/", PortalDepartmentDetailView.as_view()),
    path("portal/doctors/", PortalDoctorListView.as_view()),
    path("portal/doctors/<int:user_id>/", PortalDoctorDetailView.as_view()),
    path("doctor/content/profile/me/", DoctorProfileMeView.as_view()),
    path("doctor/content/profile/me/submit-review/", DoctorSubmitReviewView.as_view()),
    path("admin/content/", include(admin_router.urls)),
    path(
        "admin/content/doctor-profiles/<int:user_id>/departments/",
        AdminDoctorDepartmentsView.as_view(),
    ),
    path(
        "admin/content/doctor-profiles/<int:user_id>/approve/",
        AdminApproveDoctorView.as_view(),
    ),
    path(
        "admin/content/doctor-profiles/<int:user_id>/reject/",
        AdminRejectDoctorView.as_view(),
    ),
    path("admin/content/pending-reviews/", AdminPendingReviewsView.as_view()),
    path("media/upload/", MediaUploadView.as_view()),
]
