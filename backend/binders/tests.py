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

    def test_add_card_by_id_with_quantity(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=1)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-card-by-id", args=[binder.pk])
        response = self.client.post(url, {"card_id": self.card1.id, "quantity": 3}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BinderCard.objects.get(binder=binder, card=self.card1).quantity, 4)

    def test_add_card_by_id_rejects_invalid_quantity(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-card-by-id", args=[binder.pk])
        for bad in (0, -2, "abc", 1000):
            response = self.client.post(url, {"card_id": self.card1.id, "quantity": bad}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad)
        self.assertFalse(BinderCard.objects.filter(binder=binder).exists())

    def test_add_card_by_id_with_condition_and_language(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=2)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-card-by-id", args=[binder.pk])
        payload = {"card_id": self.card1.id, "quantity": 1, "condition": "SP", "language": "ES"}
        self.client.post(url, payload, format="json")
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = {
            (bc.condition, bc.language): bc.quantity
            for bc in BinderCard.objects.filter(binder=binder, card=self.card1)
        }
        self.assertEqual(rows, {('NM', 'EN'): 2, ('SP', 'ES'): 2})

    def test_add_card_by_id_rejects_unknown_condition_or_language(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-add-card-by-id", args=[binder.pk])
        for extra in ({"condition": "XX"}, {"language": "klingon"}):
            response = self.client.post(url, {"card_id": self.card1.id, **extra}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, extra)
        self.assertFalse(BinderCard.objects.filter(binder=binder).exists())

    def test_binder_lists_each_condition_language_row_separately(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=2)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=1, condition='HP', language='JA')

        response = self.client.get(reverse("binders:binder-detail", args=[binder.pk]))

        card_set = response.data['card_set']
        self.assertEqual(len(card_set), 2)
        self.assertEqual(len({c['binder_card_id'] for c in card_set}), 2)
        self.assertEqual(response.data['copy_count'], 3)

    def test_remove_cards_with_several_rows_for_the_name(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=1)
        BinderCard.objects.create(binder=binder, card=self.card1, quantity=1, condition='SP')
        self.client.force_authenticate(user=self.user)

        url = reverse("binders:binder-remove-cards", args=[binder.pk])
        response = self.client.post(url, {"card_names": [self.card1.name]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BinderCard.objects.filter(binder=binder, card=self.card1).count(), 1)

    def test_import_moxfield_reads_condition_and_language(self):
        binder = Binder.objects.create(name="My Binder", user=self.user)
        self.client.force_authenticate(user=self.user)

        csv_data = (
            "Count,Name,Edition,Condition,Language,Foil,Collector Number\n"
            f"2,{self.card1.name},Set,Near Mint,English,,1\n"
            f"1,{self.card1.name},Set,Lightly Played,Japanese,,1\n"
            f"1,{self.card2.name},Set,Weird,Klingon,,2\n"
        )
        url = reverse("binders:binder-import-moxfield", args=[binder.pk])
        self.client.post(url, {"csv_data": csv_data}, format="json")

        rows = {
            (bc.card_id, bc.condition, bc.language): bc.quantity
            for bc in BinderCard.objects.filter(binder=binder)
        }
        self.assertEqual(rows, {
            (self.card1.id, 'NM', 'EN'): 2,
            (self.card1.id, 'SP', 'JA'): 1,
            (self.card2.id, 'NM', 'EN'): 1,
        })

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

    def test_import_moxfield_only_needs_count_name_and_foil(self):
        """Count/Name/Foil carry the import; the rest of Moxfield's columns are decoration."""
        binder = Binder.objects.create(name="Minimal", user=self.user)
        self.client.force_authenticate(user=self.user)

        csv_data = (
            "Count,Name,Foil\n"
            f"4,{self.card1.name},\n"
            f"1,{self.card2.name},foil\n"
        )
        url = reverse("binders:binder-import-moxfield", args=[binder.pk])
        response = self.client.post(url, {"csv_data": csv_data}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['not_found'], [])

        bc1 = BinderCard.objects.get(binder=binder, card=self.card1)
        self.assertEqual(bc1.quantity, 4)
        self.assertFalse(bc1.foil)

        bc2 = BinderCard.objects.get(binder=binder, card=self.card2)
        self.assertTrue(bc2.foil)

    def test_import_moxfield_accepts_every_documented_foil_spelling(self):
        binder = Binder.objects.create(name="Foils", user=self.user)
        self.client.force_authenticate(user=self.user)
        url = reverse("binders:binder-import-moxfield", args=[binder.pk])

        for marker in ('foil', 'yes', 'true', '1', 'FOIL'):
            BinderCard.objects.filter(binder=binder).delete()
            response = self.client.post(
                url,
                {"csv_data": f"Count,Name,Foil\n1,{self.card1.name},{marker}\n"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(
                BinderCard.objects.get(binder=binder, card=self.card1).foil,
                f'"{marker}" should mark the card as foil',
            )


class BinderCardQuantityTestCase(APITestCase):
    """A binder's cards carry how many copies it holds, so a buyer can ask for more than one."""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="testpassword")
        self.card1 = make_card("1", "Aaa Card")
        self.card2 = make_card("2", "Bbb Card")
        self.binder = Binder.objects.create(name="Binder", user=self.user, is_public=True)
        BinderCard.objects.create(binder=self.binder, card=self.card2, quantity=1)
        BinderCard.objects.create(binder=self.binder, card=self.card1, quantity=3, foil=True)

    def _cards(self):
        response = self.client.get(reverse("binders:binder-detail", args=[self.binder.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_each_card_reports_its_quantity(self):
        by_id = {c['id']: c for c in self._cards()['card_set']}

        self.assertEqual(by_id['1']['quantity'], 3)
        self.assertEqual(by_id['2']['quantity'], 1)

    def test_condition_and_language_default_and_travel_with_the_card(self):
        BinderCard.objects.filter(binder=self.binder, card=self.card2).update(
            condition='MP', language='ES',
        )
        by_id = {c['id']: c for c in self._cards()['card_set']}

        # card1 was created without either, so it takes the defaults.
        self.assertEqual(by_id['1']['condition'], 'NM')
        self.assertEqual(by_id['1']['condition_display'], 'Near Mint')
        self.assertEqual(by_id['1']['language'], 'EN')
        self.assertEqual(by_id['1']['language_display'], 'Inglés')

        self.assertEqual(by_id['2']['condition_display'], 'Moderately Played')
        self.assertEqual(by_id['2']['language_display'], 'Español')

    def test_collector_number_is_exposed(self):
        Card.objects.filter(pk='1').update(collector_number='264')
        by_id = {c['id']: c for c in self._cards()['card_set']}

        self.assertEqual(by_id['1']['collector_number'], '264')
        self.assertEqual(by_id['2']['collector_number'], '')

    def test_foil_and_etched_travel_with_the_card(self):
        by_id = {c['id']: c for c in self._cards()['card_set']}

        self.assertTrue(by_id['1']['foil'])
        self.assertFalse(by_id['1']['etched'])
        self.assertFalse(by_id['2']['foil'])

    def test_cards_come_back_ordered_by_name(self):
        self.assertEqual([c['name'] for c in self._cards()['card_set']], ["Aaa Card", "Bbb Card"])

    def test_card_count_counts_cards_and_copy_count_counts_copies(self):
        data = self._cards()

        self.assertEqual(data['card_count'], 2)
        self.assertEqual(data['copy_count'], 4)

    def test_quantity_survives_the_list_endpoint(self):
        response = self.client.get(reverse("binders:binder-list"))

        binder = next(b for b in response.data if b['id'] == self.binder.pk)
        self.assertEqual({c['id']: c['quantity'] for c in binder['card_set']}, {'1': 3, '2': 1})


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
