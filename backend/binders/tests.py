from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from binders.models import Binder, BinderCard, WishlistCard
from cards.models import Card


def make_card(id, name, **kwargs):
    defaults = {
        'set_name': 'Set',
        'set_code': 'set',
        'color_identity': 'R',
        'uri': f'uri{id}',
        'scryfall_uri': f'scryfall_uri{id}',
        'image_uri': f'http://image{id}.com',
    }
    defaults.update(kwargs)
    return Card.objects.create(id=id, name=name, **defaults)


class BinderViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.other_user = User.objects.create_user(username="otheruser", password="testpassword")

        self.card1 = make_card("1", "Card One")
        self.card2 = make_card("2", "Card Two")
        self.card3 = make_card("3", "Card Three")

    def test_list_is_public_and_excludes_private_binders(self):
        Binder.objects.create(name="Public Binder", user=self.user, is_public=True)
        Binder.objects.create(name="Private Binder", user=self.user, is_public=False)

        url = reverse("binders:binder-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [b['name'] for b in response.data]
        self.assertIn("Public Binder", names)
        self.assertNotIn("Private Binder", names)

    def test_list_filters_by_card_name(self):
        binder = Binder.objects.create(name="Has Card One", user=self.user, is_public=True)
        BinderCard.objects.create(binder=binder, card=self.card1)
        other = Binder.objects.create(name="No Match", user=self.user, is_public=True)
        BinderCard.objects.create(binder=other, card=self.card2)

        url = reverse("binders:binder-list")
        response = self.client.get(url, {'card_name': 'Card One'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [b['name'] for b in response.data]
        self.assertIn("Has Card One", names)
        self.assertNotIn("No Match", names)

    def test_create_binder_requires_auth(self):
        url = reverse("binders:binder-list")
        response = self.client.post(url, {"name": "My Binder"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_binder(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("binders:binder-list")
        response = self.client.post(url, {"name": "My Binder"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        binder = Binder.objects.get(name="My Binder")
        self.assertEqual(binder.user, self.user)

    def test_cannot_update_binder_of_another_user(self):
        binder = Binder.objects.create(name="Original", user=self.other_user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-detail", args=[binder.pk])
        response = self.client.patch(url, {"name": "Hijacked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        binder.refresh_from_db()
        self.assertEqual(binder.name, "Original")

    def test_cannot_delete_binder_of_another_user(self):
        binder = Binder.objects.create(name="Original", user=self.other_user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-detail", args=[binder.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Binder.objects.filter(pk=binder.pk).exists())

    def test_my_binders_only_returns_own(self):
        Binder.objects.create(name="Mine", user=self.user)
        Binder.objects.create(name="Theirs", user=self.other_user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-my-binders")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [b['name'] for b in response.data]
        self.assertEqual(names, ["Mine"])

    def test_add_cards_by_name(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-cards", args=[binder.pk])
        response = self.client.post(url, {"card_names": [self.card1.name, self.card1.name, self.card2.name]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['not_found'], [])

        self.assertEqual(BinderCard.objects.get(binder=binder, card=self.card1).quantity, 2)
        self.assertEqual(BinderCard.objects.get(binder=binder, card=self.card2).quantity, 1)

    def test_add_cards_requires_ownership(self):
        binder = Binder.objects.create(name="Not Mine", user=self.other_user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-cards", args=[binder.pk])
        response = self.client.post(url, {"card_names": [self.card1.name]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_card_by_id(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-card-by-id", args=[binder.pk])
        response = self.client.post(url, {"card_id": self.card1.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BinderCard.objects.get(binder=binder, card=self.card1).quantity, 1)

    def test_remove_cards(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=2)
        BinderCard.objects.create(binder=binder, card=self.card2, quantity=1)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-remove-cards", args=[binder.pk])
        response = self.client.post(url, {"card_names": [self.card1.name, self.card2.name]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BinderCard.objects.get(binder=binder, card=self.card1).quantity, 1)
        self.assertFalse(BinderCard.objects.filter(binder=binder, card=self.card2).exists())

    def test_import_moxfield(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        csv_data = (
            "Count,Name,Edition,Condition,Language,Foil,Collector Number\n"
            f"3,{self.card1.name},Set,Near Mint,English,,1\n"
            f"1,{self.card2.name},Set,Near Mint,English,foil,2\n"
        )
        url = reverse("binders:binder-import-moxfield", args=[binder.pk])
        response = self.client.post(url, {"csv_data": csv_data}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['not_found'], [])

        bc1 = BinderCard.objects.get(binder=binder, card=self.card1)
        self.assertEqual(bc1.quantity, 3)
        self.assertFalse(bc1.foil)

        bc2 = BinderCard.objects.get(binder=binder, card=self.card2)
        self.assertEqual(bc2.quantity, 1)
        self.assertTrue(bc2.foil)


class WishlistViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="wisher", password="testpassword")
        self.owner = User.objects.create_user(username="owner", password="testpassword")
        self.card1 = make_card("1", "Card One")
        self.card2 = make_card("2", "Card Two")

    def test_requires_auth(self):
        url = reverse("binders:wishlist-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_and_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("binders:wishlist-list")

        response = self.client.post(url, {"card_names": [self.card1.name]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WishlistCard.objects.filter(user=self.user, card=self.card1).count(), 1)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['card']['id'], self.card1.id)

    def test_destroy(self):
        WishlistCard.objects.create(user=self.user, card=self.card1)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:wishlist-detail", args=[self.card1.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishlistCard.objects.filter(user=self.user, card=self.card1).exists())

    def test_matches_finds_other_public_binders(self):
        WishlistCard.objects.create(user=self.user, card=self.card1)
        WishlistCard.objects.create(user=self.user, card=self.card2)

        public_binder = Binder.objects.create(name="Owner Binder", user=self.owner, is_public=True)
        BinderCard.objects.create(binder=public_binder, card=self.card1, quantity=2)

        private_binder = Binder.objects.create(name="Owner Private", user=self.owner, is_public=False)
        BinderCard.objects.create(binder=private_binder, card=self.card2, quantity=1)

        self.client.force_authenticate(user=self.user)
        url = reverse("binders:wishlist-matches")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        match = response.data[0]
        self.assertEqual(match['username'], self.owner.username)
        self.assertEqual(match['match_count'], 1)
        self.assertEqual(match['cards'][0]['id'], self.card1.id)

    def test_matches_excludes_own_binders(self):
        WishlistCard.objects.create(user=self.user, card=self.card1)
        own_binder = Binder.objects.create(name="Mine", user=self.user, is_public=True)
        BinderCard.objects.create(binder=own_binder, card=self.card1, quantity=1)

        self.client.force_authenticate(user=self.user)
        url = reverse("binders:wishlist-matches")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
