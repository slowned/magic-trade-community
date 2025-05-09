from django.test import TestCase

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from binders.models import Binder, BinderCard, Card
from django.urls import reverse


class BinderViewSetTestCase(APITestCase):
    def setUp(self):
        # Crear un usuario y autenticar
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.user_no_login = User.objects.create_user(username="nologin", password="testpassword")

        # Crear cartas de ejemplo

        self.card1 = Card.objects.create(id="1", name="Card 1", set_name="Set 1", color_identity="R", uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com")
        self.card2 = Card.objects.create(id="2", name="Card 2", set_name="Set 2", color_identity="G", uri="uri2", scryfall_uri="scryfall_uri2", image_uri="http://image2.com")
        self.card3 = Card.objects.create(id="3", name="Card 3", set_name="Set 2", color_identity="B", uri="uri2", scryfall_uri="scryfall_uri3", image_uri="http://image3.com")

    #TODO: TESTEAR Q ESTE LOGEADO
    def test_create_binder(self):
        # Test para crear un nuevo binder
        url = reverse("binder:binder-list")
        data = {"name": "My Binder", "user": self.user.id}

        # connect = self.client.login(username=self.user.username, password=self.user.password)
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Binder.objects.count(), 1)
        self.assertEqual(Binder.objects.get().name, "My Binder")
        self.client.logout()

    #TODO: TESTEAR Q ESTE LOGEADO
    # def test_fail_create_binder_no_login_user(self):
    #     url = reverse("binder:binder-list")
    #     data = {"name": "My Binder", "user": self.user_no_login.id}

    #     response = self.client.post(url, data, format="json")

    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_cards_to_binder(self):
        # Crear un binder
        binder = Binder.objects.create(name="My Binder", user=self.user)
        # Añadir cartas al binder

        url = reverse("binder:binder-add-card", kwargs={"pk": binder.pk})

        card_1_quantity = 1
        card_2_quantity = 3
        data = {
                "cards": [
                    {"card_id": self.card1.id, "quantity": card_1_quantity},
                    {"card_id": self.card2.id, "quantity": card_2_quantity},
                ],
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(self.card1, binder.card_set.all())

        card_quantity = BinderCard.objects.get(card=self.card1, binder=binder).quantity
        self.assertEqual(card_quantity, card_1_quantity)

        card_quantity = BinderCard.objects.get(card=self.card2, binder=binder).quantity
        self.assertEqual(card_quantity, card_2_quantity)
        # ver cuantas repeticones hay de card_2
        # binder.card_set.get(id=self.card2.id).count()

        card_1_plus = 5
        data = {
                "cards": [
                    {"card_id": self.card1.id, "quantity": card_1_plus},
                ],
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        card_quantity = BinderCard.objects.get(card=self.card1, binder=binder).quantity
        self.assertEqual(card_quantity, card_1_quantity + card_1_plus)

    def test_remove_cards_from_binder(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        url = reverse("binder:binder-add-card", kwargs={"pk": binder.pk})

        card_1_quantity = 2
        card_2_quantity = 3
        data = {
                "cards": [
                    {"card_id": self.card1.id, "quantity": card_1_quantity},
                    {"card_id": self.card2.id, "quantity": card_2_quantity},
                ]
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # cards to remove
        card_1_to_remove = 1
        card_2_to_remove = 3
        data = {
                "cards": [
                    {"card_id": self.card1.id, "quantity": card_1_to_remove},
                    {"card_id": self.card2.id, "quantity": card_2_to_remove},
                ]
        }

        url = reverse("binder:binder-remove-card", kwargs={"pk": binder.pk})
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        card_quantity = BinderCard.objects.get(binder__id=binder.id, card__id=self.card1.id).quantity
        self.assertEqual(card_quantity, card_1_quantity - card_1_to_remove)

        card_quantity = BinderCard.objects.get(binder__id=binder.id, card__id=self.card2.id).quantity
        self.assertNotInl(self.card2.id, binder.card_set.all())

    def test_remove_card_does_not_exist_in_binder(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        url = reverse("binder:binder-add-card", kwargs={"pk": binder.pk})

        card_1_quantity = 3

        data = {
                "cards": [
                    {"card_id": self.card1.id, "quantity": card_1_quantity},
                ]
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # cards to remove
        card_3_to_remove = 1
        data = {
                "cards": [
                    {"card_id": self.card3.id, "quantity": card_3_to_remove},
                ]
        }

        url = reverse("binder:binder-remove-card", kwargs={"pk": binder.pk})
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
