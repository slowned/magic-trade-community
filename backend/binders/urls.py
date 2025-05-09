from django.urls import include, path
from rest_framework.routers import DefaultRouter

from binders.views import BinderViewSet

router = DefaultRouter()

router.register(
    "binders",
    BinderViewSet,
)

app_name = "binders"

urlpatterns = [path(f"{app_name}/", include(router.urls))]
