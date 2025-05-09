from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet

router = DefaultRouter()

router.register(
    "users",
    UserViewSet,
)

app_name = "users"

urlpatterns = [path(f"{app_name}/", include(router.urls))]
