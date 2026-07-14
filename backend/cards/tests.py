from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from binders.models import Card


class CheckCardsViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpassword")
        Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )

    def test_requires_auth(self):
        url = reverse("check-cards")
        response = self.client.post(url, {"names": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_splits_existing_and_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("check-cards")

        response = self.client.post(url, {"names": ["Card One", "Nonexistent Card"]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["existing_cards"], ["Card One"])
        self.assertEqual(response.data["not_found"], ["Nonexistent Card"])

    def test_rejects_non_list_names(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("check-cards")

        response = self.client.post(url, {"names": "Card One"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CardAutocompleteViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpassword")

    def test_requires_auth(self):
        url = reverse("card-autocomplete")
        response = self.client.get(url, {"q": "bla"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_short_query_returns_empty_without_calling_scryfall(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("card-autocomplete")

        with patch("mtg_trade_community.scryfall.Scryfall.autocomplete") as mock_autocomplete:
            response = self.client.get(url, {"q": "b"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        mock_autocomplete.assert_not_called()

    def test_delegates_to_scryfall(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("card-autocomplete")

        with patch("mtg_trade_community.scryfall.Scryfall.autocomplete", return_value=["Black Lotus", "Black Knight"]) as mock_autocomplete:
            response = self.client.get(url, {"q": "black"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ["Black Lotus", "Black Knight"])
        mock_autocomplete.assert_called_once_with("black")
