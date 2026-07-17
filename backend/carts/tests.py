from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from binders.models import Binder, BinderCard
from cards.models import Card
from carts.models import Cart, CartItem, Order, Rating


class CartViewSetTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
            price_usd="10.00",
        )
        self.binder = Binder.objects.create(name="Seller Binder", user=self.seller, is_public=True)
        self.bindercard = BinderCard.objects.create(binder=self.binder, card=self.card, quantity=1)

    def _add_card(self, quantity=1):
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-add-card")
        return self.client.post(url, {
            'seller_username': self.seller.username,
            'card_id': self.card.id,
            'quantity': quantity,
        }, format="json")

    def test_add_card_requires_auth(self):
        url = reverse("carts:carts-add-card")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_card_creates_cart_and_item(self):
        response = self._add_card(quantity=2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart = Cart.objects.get(buyer=self.buyer, seller=self.seller)
        item = CartItem.objects.get(cart=cart, card=self.card)
        self.assertEqual(item.quantity, 2)

    def test_add_card_reuses_open_cart(self):
        self._add_card(quantity=1)
        self._add_card(quantity=1)

        self.assertEqual(Cart.objects.filter(buyer=self.buyer, seller=self.seller).count(), 1)
        cart = Cart.objects.get(buyer=self.buyer, seller=self.seller)
        item = CartItem.objects.get(cart=cart, card=self.card)
        self.assertEqual(item.quantity, 2)

    def test_add_card_blocks_self_trading(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("carts:carts-add-card")
        response = self.client.post(url, {
            'seller_username': self.seller.username,
            'card_id': self.card.id,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_card_rejects_when_seller_no_longer_has_it(self):
        self.bindercard.delete()
        response = self._add_card()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(Cart.objects.filter(buyer=self.buyer, seller=self.seller).exists())

    def test_add_card_rejects_when_binder_is_private(self):
        self.binder.is_public = False
        self.binder.save()
        response = self._add_card()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class CheckoutTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
            price_usd="10.00",
        )
        self.binder = Binder.objects.create(name="Seller Binder", user=self.seller, is_public=True)
        self.bindercard = BinderCard.objects.create(binder=self.binder, card=self.card, quantity=1)

        self.cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)
        CartItem.objects.create(cart=self.cart, card=self.card, quantity=1)

    def _checkout(self, **overrides):
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-checkout", args=[self.cart.pk])
        data = {'shipping_method': 'door_to_door'}
        data.update(overrides)
        return self.client.post(url, data, format="json")

    def test_checkout_requires_valid_shipping_method(self):
        response = self._checkout(shipping_method='teleport')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_success_creates_order_and_clears_seller_binder(self):
        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.cart.refresh_from_db()
        self.assertTrue(self.cart.is_finalized)
        self.assertTrue(Order.objects.filter(cart=self.cart).exists())
        self.assertFalse(BinderCard.objects.filter(pk=self.bindercard.pk).exists())

    def test_checkout_blocks_when_card_no_longer_available(self):
        """Race-condition guard: seller sold the card elsewhere before checkout."""
        self.bindercard.delete()

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['unavailable_cards'], [{'id': self.card.id, 'name': self.card.name}])
        self.cart.refresh_from_db()
        self.assertFalse(self.cart.is_finalized)
        self.assertFalse(Order.objects.filter(cart=self.cart).exists())

    def test_checkout_empty_cart_rejected(self):
        empty_cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-checkout", args=[empty_cart.pk])

        response = self.client.post(url, {'shipping_method': 'door_to_door'}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_twice_rejected(self):
        self._checkout()
        response = self._checkout()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderStatusTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.other = User.objects.create_user(username="other", password="testpassword")
        card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )
        self.cart = Cart.objects.create(buyer=self.buyer, seller=self.seller, is_finalized=True)
        CartItem.objects.create(cart=self.cart, card=card, quantity=1)
        self.order = Order.objects.create(cart=self.cart, shipping_method='door_to_door')

    def _set_status(self, user, new_status):
        self.client.force_authenticate(user=user)
        url = reverse("carts:carts-update-status", args=[self.cart.pk])
        return self.client.post(url, {'status': new_status}, format="json")

    def test_seller_can_mark_shipped(self):
        response = self._set_status(self.seller, 'shipped')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')

    def test_buyer_cannot_mark_shipped(self):
        response = self._set_status(self.buyer, 'shipped')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_can_mark_completed(self):
        response = self._set_status(self.buyer, 'completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')

    def test_seller_cannot_mark_completed(self):
        response = self._set_status(self.seller, 'completed')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_see_or_update_order(self):
        response = self._set_status(self.other, 'shipped')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RatingTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )
        self.cart = Cart.objects.create(buyer=self.buyer, seller=self.seller, is_finalized=True)
        CartItem.objects.create(cart=self.cart, card=card, quantity=3)
        self.order = Order.objects.create(cart=self.cart, shipping_method='door_to_door', status='completed')

    def _rate(self, user, score, comment=''):
        self.client.force_authenticate(user=user)
        url = reverse("carts:carts-rate", args=[self.cart.pk])
        return self.client.post(url, {'score': score, 'comment': comment}, format="json")

    def test_buyer_can_rate_completed_order(self):
        response = self._rate(self.buyer, 9, comment='Todo perfecto')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rating = Rating.objects.get(order=self.order)
        self.assertEqual(rating.score, 9)
        self.assertEqual(rating.rater, self.buyer)
        self.assertEqual(rating.ratee, self.seller)
        self.assertEqual(response.data['order']['rating']['score'], 9)

    def test_seller_cannot_rate(self):
        response = self._rate(self.seller, 5)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_rate_pending_order(self):
        self.order.status = 'pending'
        self.order.save()
        response = self._rate(self.buyer, 8)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_rate_twice(self):
        self._rate(self.buyer, 9)
        response = self._rate(self.buyer, 2)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Rating.objects.get(order=self.order).score, 9)

    def test_score_out_of_range_rejected(self):
        self.assertEqual(self._rate(self.buyer, 11).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._rate(self.buyer, -1).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._rate(self.buyer, 'diez').status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_is_a_valid_score(self):
        response = self._rate(self.buyer, 0)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.get(order=self.order).score, 0)


class CartMessagesTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.outsider = User.objects.create_user(username="outsider", password="testpassword")
        self.cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)

    def test_participant_can_post_and_list_messages(self):
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-messages", args=[self.cart.pk])

        response = self.client.post(url, {'content': 'Hola, sigue disponible?'}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.seller)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'Hola, sigue disponible?')
        self.assertEqual(response.data[0]['sender'], 'buyer')

    def test_outsider_cannot_access_messages(self):
        self.client.force_authenticate(user=self.outsider)
        url = reverse("carts:carts-messages", args=[self.cart.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_message_rejected(self):
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-messages", args=[self.cart.pk])

        response = self.client.post(url, {'content': '   '}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
