from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssistantViewSet,
    DeviceBindingViewSet,
    ProvisionRequestViewSet,
    PublicPlanViewSet,
    complete_device_pairing,
    csrf,
    health,
    login_view,
    logout_view,
    me,
    register,
    request_email_code,
    verify_email_code,
)

router = DefaultRouter()
router.register("assistants", AssistantViewSet, basename="assistant")
router.register("devices", DeviceBindingViewSet, basename="device")
router.register("provision-requests", ProvisionRequestViewSet, basename="provision-request")
router.register("public/plans", PublicPlanViewSet, basename="public-plan")

urlpatterns = [
    path("health/", health, name="health"),
    path("csrf/", csrf, name="csrf"),
    path("auth/me/", me, name="me"),
    path("auth/register/", register, name="register"),
    path("auth/login/", login_view, name="login"),
    path("auth/email-code/request/", request_email_code, name="request-email-code"),
    path("auth/email-code/verify/", verify_email_code, name="verify-email-code"),
    path("auth/logout/", logout_view, name="logout"),
    path("agent/pair-device/", complete_device_pairing, name="complete-device-pairing"),
    path("", include(router.urls)),
]
