import base64
import io

from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from binders.models import Card
from scanner.views import _compute_hash


def _make_frame_b64(color):
    """Build a solid-color JPEG frame and return (base64_string, resulting_dhash)."""
    image = Image.new('RGB', (400, 560), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    jpeg_bytes = buffer.getvalue()

    # Hash the same round-tripped bytes the view will decode, so JPEG
    # compression artifacts can't cause a mismatch.
    decoded = Image.open(io.BytesIO(jpeg_bytes)).convert('RGB')
    expected_hash = _compute_hash(decoded)

    return base64.b64encode(jpeg_bytes).decode(), expected_hash


class CardIdentifyViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="scanner_user", password="testpassword")

    def test_requires_auth(self):
        url = reverse("scanner-identify")
        response = self.client.post(url, {"image": "irrelevant"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_image_field(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("scanner-identify")

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_image_data(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("scanner-identify")

        response = self.client.post(url, {"image": "not-valid-base64!!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_match_when_no_cards_hashed(self):
        image_b64, _ = _make_frame_b64((10, 20, 30))
        Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
            phash='',
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("scanner-identify")

        response = self.client.post(url, {"image": image_b64}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['card'])

    def test_exact_match_returns_card_with_zero_distance(self):
        image_b64, expected_hash = _make_frame_b64((200, 60, 60))
        card = Card.objects.create(
            id="1", name="Lightning Bolt", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
            phash=expected_hash,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("scanner-identify")

        response = self.client.post(url, {"image": image_b64}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['card']['id'], card.id)
        self.assertEqual(response.data['distance'], 0)
        self.assertEqual(response.data['confidence'], 1.0)
