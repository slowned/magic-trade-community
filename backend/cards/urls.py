from django.urls import path
from .views import CheckCardsView, CardAutocompleteView

urlpatterns = [
    path('cards/check-cards/', CheckCardsView.as_view(), name='check-cards'),
    path('cards/autocomplete/', CardAutocompleteView.as_view(), name='card-autocomplete'),
]
