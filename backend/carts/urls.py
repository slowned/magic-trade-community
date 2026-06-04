from django.urls import include, path
from rest_framework.routers import DefaultRouter

from carts.views import CartViewSet

router = DefaultRouter()
router.register('carts', CartViewSet, basename='carts')

app_name = 'carts'

urlpatterns = [path(f'{app_name}/', include(router.urls))]
