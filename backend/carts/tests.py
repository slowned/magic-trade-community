import threading

from django.contrib.auth.models import User
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from binders.models import Binder, BinderCard
from cards.models import Card
from carts.models import Cart, CartItem, CartItemAllocation, Order, Rating


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
        self.bindercard = BinderCard.objects.create(binder=self.binder, card=self.card, quantity=4)

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

    def test_add_card_caps_at_available_quantity(self):
        response = self._add_card(quantity=5)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['available'], 4)
        self.assertFalse(Cart.objects.filter(buyer=self.buyer, seller=self.seller).exists())

    def test_add_card_cap_counts_copies_already_in_the_cart(self):
        self._add_card(quantity=3)
        response = self._add_card(quantity=2)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        item = CartItem.objects.get(cart__buyer=self.buyer, card=self.card)
        self.assertEqual(item.quantity, 3)

    def test_add_card_cap_sums_across_public_binders(self):
        other = Binder.objects.create(name="Second", user=self.seller, is_public=True)
        BinderCard.objects.create(binder=other, card=self.card, quantity=2)

        response = self._add_card(quantity=6)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_card_cap_ignores_private_binders(self):
        private = Binder.objects.create(name="Personal", user=self.seller, is_public=False)
        BinderCard.objects.create(binder=private, card=self.card, quantity=10)

        response = self._add_card(quantity=5)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['available'], 4)


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
        return self.client.post(url, dict(overrides), format="json")

    def test_checkout_rejects_an_invalid_shipping_method(self):
        response = self._checkout(shipping_method='teleport')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_needs_no_shipping_method(self):
        """It's agreed in the order chat, so the order starts without one."""
        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.get(cart=self.cart).shipping_method, '')

    def test_checkout_still_records_a_shipping_method_when_sent(self):
        response = self._checkout(shipping_method='branch_pickup')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.get(cart=self.cart).shipping_method, 'branch_pickup')

    def test_checkout_success_creates_order_and_clears_seller_binder(self):
        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.cart.refresh_from_db()
        self.assertTrue(self.cart.is_finalized)
        self.assertTrue(Order.objects.filter(cart=self.cart).exists())
        self.assertFalse(BinderCard.objects.filter(pk=self.bindercard.pk).exists())

    def test_checkout_blocks_when_card_no_longer_available(self):
        """First checkout wins: someone else bought the last copy first."""
        self.bindercard.delete()

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['unavailable_cards'], [
            {'id': self.card.id, 'name': self.card.name, 'requested': 1, 'available': 0},
        ])
        self.cart.refresh_from_db()
        self.assertFalse(self.cart.is_finalized)
        self.assertFalse(Order.objects.filter(cart=self.cart).exists())

    def test_checkout_decrements_quantity_instead_of_wiping_the_row(self):
        self.bindercard.quantity = 4
        self.bindercard.save()

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.bindercard.refresh_from_db()
        self.assertEqual(self.bindercard.quantity, 3)

    def test_checkout_leaves_the_sellers_other_binders_alone(self):
        personal = Binder.objects.create(name="Personal", user=self.seller, is_public=False)
        kept = BinderCard.objects.create(binder=personal, card=self.card, quantity=2)

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        kept.refresh_from_db()
        self.assertEqual(kept.quantity, 2)
        self.assertFalse(BinderCard.objects.filter(pk=self.bindercard.pk).exists())

    def test_checkout_blocks_when_only_private_copies_remain(self):
        self.bindercard.delete()
        personal = Binder.objects.create(name="Personal", user=self.seller, is_public=False)
        BinderCard.objects.create(binder=personal, card=self.card, quantity=3)

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(Order.objects.filter(cart=self.cart).exists())

    def test_checkout_blocks_on_partial_stock_without_deducting(self):
        CartItem.objects.filter(cart=self.cart, card=self.card).update(quantity=3)

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['unavailable_cards'][0]['available'], 1)
        self.bindercard.refresh_from_db()
        self.assertEqual(self.bindercard.quantity, 1)

    def test_checkout_draws_from_several_binders(self):
        second = Binder.objects.create(name="Second", user=self.seller, is_public=True)
        BinderCard.objects.create(binder=second, card=self.card, quantity=2)
        CartItem.objects.filter(cart=self.cart, card=self.card).update(quantity=3)

        response = self._checkout()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            BinderCard.objects.filter(binder__user=self.seller, card=self.card).count(), 0
        )
        allocations = CartItemAllocation.objects.filter(item__cart=self.cart)
        self.assertEqual(allocations.count(), 2)
        self.assertEqual(sum(a.quantity for a in allocations), 3)

    def test_auction_cart_checkout_touches_no_binder_stock(self):
        auction_cart = Cart.objects.create(
            buyer=self.buyer, seller=self.seller, source=Cart.SOURCE_AUCTION,
        )
        CartItem.objects.create(cart=auction_cart, card=self.card, quantity=1, price_ars="5000.00")

        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-checkout", args=[auction_cart.pk])
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.bindercard.refresh_from_db()
        self.assertEqual(self.bindercard.quantity, 1)
        self.assertFalse(CartItemAllocation.objects.filter(item__cart=auction_cart).exists())

    def test_checkout_empty_cart_rejected(self):
        empty_cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)
        self.client.force_authenticate(user=self.buyer)
        url = reverse("carts:carts-checkout", args=[empty_cart.pk])

        response = self.client.post(url, {}, format="json")
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


class CancellationRestoresStockTestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="testpassword")
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )
        self.binder = Binder.objects.create(name="Seller Binder", user=self.seller, is_public=True)
        BinderCard.objects.create(binder=self.binder, card=self.card, quantity=2, foil=True)

        self.cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)
        CartItem.objects.create(cart=self.cart, card=self.card, quantity=2)

        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse("carts:carts-checkout", args=[self.cart.pk]), {}, format="json",
        )

    def _cancel(self):
        self.client.force_authenticate(user=self.buyer)
        return self.client.post(
            reverse("carts:carts-update-status", args=[self.cart.pk]),
            {'status': 'cancelled'}, format="json",
        )

    def test_cancelling_puts_the_cards_back(self):
        self.assertFalse(BinderCard.objects.filter(binder=self.binder, card=self.card).exists())

        response = self._cancel()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        restored = BinderCard.objects.get(binder=self.binder, card=self.card)
        self.assertEqual(restored.quantity, 2)
        self.assertTrue(restored.foil)

    def test_restore_adds_to_a_row_the_seller_recreated(self):
        BinderCard.objects.create(binder=self.binder, card=self.card, quantity=1)

        self._cancel()

        self.assertEqual(
            BinderCard.objects.get(binder=self.binder, card=self.card).quantity, 3
        )

    def test_restore_keeps_condition_and_language(self):
        """A cancelled SP Spanish copy goes back as SP Spanish, not as a new NM English row."""
        Cart.objects.all().delete()
        BinderCard.objects.create(
            binder=self.binder, card=self.card, quantity=1, condition='SP', language='ES',
        )
        cart = Cart.objects.create(buyer=self.buyer, seller=self.seller)
        CartItem.objects.create(cart=cart, card=self.card, quantity=1)
        self.client.force_authenticate(user=self.buyer)
        self.client.post(reverse("carts:carts-checkout", args=[cart.pk]), {}, format="json")
        self.assertFalse(BinderCard.objects.filter(binder=self.binder).exists())

        self.client.post(
            reverse("carts:carts-update-status", args=[cart.pk]),
            {'status': 'cancelled'}, format="json",
        )

        restored = BinderCard.objects.get(binder=self.binder, card=self.card)
        self.assertEqual((restored.condition, restored.language, restored.quantity), ('SP', 'ES', 1))

    def test_restoring_is_idempotent(self):
        self._cancel()
        self._cancel()

        self.assertEqual(
            BinderCard.objects.get(binder=self.binder, card=self.card).quantity, 2
        )
        self.assertFalse(CartItemAllocation.objects.filter(item__cart=self.cart).exists())

    def test_completing_an_order_restores_nothing(self):
        self.client.force_authenticate(user=self.buyer)
        self.client.post(
            reverse("carts:carts-update-status", args=[self.cart.pk]),
            {'status': 'completed'}, format="json",
        )

        self.assertFalse(BinderCard.objects.filter(binder=self.binder, card=self.card).exists())

    def test_deleted_binder_is_simply_not_restored(self):
        self.binder.delete()

        response = self._cancel()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(BinderCard.objects.filter(card=self.card).exists())


class ConcurrentCheckoutTestCase(TransactionTestCase):
    """Two buyers, one copy, simultaneous checkout: exactly one order exists.

    Needs TransactionTestCase — the threads run real transactions, which the
    single wrapping transaction of APITestCase would hide from each other.
    """

    def setUp(self):
        self.seller = User.objects.create_user(username="seller", password="testpassword")
        self.card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )
        binder = Binder.objects.create(name="Seller Binder", user=self.seller, is_public=True)
        BinderCard.objects.create(binder=binder, card=self.card, quantity=1)

        self.carts = []
        for name in ("buyer_a", "buyer_b"):
            buyer = User.objects.create_user(username=name, password="testpassword")
            cart = Cart.objects.create(buyer=buyer, seller=self.seller)
            CartItem.objects.create(cart=cart, card=self.card, quantity=1)
            self.carts.append((buyer, cart))

    def test_only_one_of_two_racing_buyers_gets_the_last_copy(self):
        start = threading.Barrier(len(self.carts))
        codes = []
        lock = threading.Lock()

        def checkout(buyer, cart):
            client = APIClient()
            client.force_authenticate(user=buyer)
            url = reverse("carts:carts-checkout", args=[cart.pk])
            try:
                start.wait(timeout=10)
                response = client.post(url, {}, format="json")
                with lock:
                    codes.append(response.status_code)
            finally:
                # Each thread opened its own connection; leaving it dangling
                # blocks the test database teardown.
                connection.close()

        threads = [threading.Thread(target=checkout, args=pair) for pair in self.carts]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(sorted(codes), [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(BinderCard.objects.filter(card=self.card).count(), 0)


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
