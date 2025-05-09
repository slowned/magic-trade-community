from django.urls import path
from .views import CheckCardsView

urlpatterns = [
    path('cards/check-cards/', CheckCardsView.as_view(), name='check-cards'),
]
