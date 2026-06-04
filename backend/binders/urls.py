from django.urls import include, path
from rest_framework.routers import DefaultRouter

from binders.views import BinderViewSet, WishlistViewSet

router = DefaultRouter()
router.register('binders', BinderViewSet)
router.register('wishlist', WishlistViewSet, basename='wishlist')

app_name = 'binders'

urlpatterns = [path(f'{app_name}/', include(router.urls))]
