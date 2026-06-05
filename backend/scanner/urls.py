"""URL routes for the scanner app."""
from django.urls import path
from scanner.views import CardIdentifyView

urlpatterns = [
    path('scanner/identify/', CardIdentifyView.as_view(), name='scanner-identify'),
]
