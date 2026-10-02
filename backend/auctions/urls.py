from django.urls import include, path
from rest_framework.routers import DefaultRouter

from auctions.views import AuctionViewSet

router = DefaultRouter()
router.register('auctions', AuctionViewSet, basename='auctions')

app_name = 'auctions'

urlpatterns = [path(f'{app_name}/', include(router.urls))]
