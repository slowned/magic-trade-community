from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from auctions.models import (
    ANTI_SNIPE_WINDOW,
    STATUS_CLOSED,
    STATUS_LIVE,
    STATUS_SCHEDULED,
    Auction,
    BidError,
    default_auction_window,
    settle_due_auctions,
)
from cards.models import Card
from carts.models import Cart


def make_card(card_id="c1", name="Black Lotus"):
    return Card.objects.create(
        id=card_id, name=name, set_name="Alpha", color_identity="",
        uri="uri", scryfall_uri="scryfall", image_uri="http://img",
        price_usd="10000.00",
    )


class AuctionBiddingTestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="platform", password="pw", is_staff=True)
        self.juan = User.objects.create_user(username="juan", password="pw")
        self.maria = User.objects.create_user(username="maria", password="pw")
        self.card = make_card()
        self.auction = Auction.objects.create(
            card=self.card, seller=self.staff,
            starting_price=Decimal('10000.00'), min_increment=Decimal('500.00'),
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(days=7),
            status=STATUS_LIVE,
        )

    def test_first_bid_sits_at_the_starting_price(self):
        self.auction.place_bid(self.juan, '15000')

        self.assertEqual(self.auction.current_price, Decimal('10000.00'))
        self.assertEqual(self.auction.current_leader, self.juan)
        self.assertEqual(self.auction.bid_count, 1)

    def test_first_bid_below_starting_price_is_rejected(self):
        with self.assertRaises(BidError):
            self.auction.place_bid(self.juan, '9999')

    def test_challenger_under_the_hidden_max_loses_and_pushes_price_up(self):
        self.auction.place_bid(self.juan, '15000')
        self.auction.place_bid(self.maria, '12000')

        # Juan's proxy absorbs it: price climbs to María's max + increment,
        # capped at Juan's ceiling. Juan keeps the lead.
        self.assertEqual(self.auction.current_price, Decimal('12500.00'))
        self.assertEqual(self.auction.current_leader, self.juan)

    def test_challenger_over_the_hidden_max_takes_the_lead_cheaply(self):
        self.auction.place_bid(self.juan, '12000')
        self.auction.place_bid(self.maria, '20000')

        # María pays one increment over Juan's ceiling, not her own maximum.
        self.assertEqual(self.auction.current_price, Decimal('12500.00'))
        self.assertEqual(self.auction.current_leader, self.maria)

    def test_challenger_max_below_min_next_bid_is_rejected(self):
        self.auction.place_bid(self.juan, '15000')
        with self.assertRaises(BidError):
            self.auction.place_bid(self.maria, '10400')

    def test_tie_keeps_the_earlier_bidder(self):
        self.auction.place_bid(self.juan, '15000')
        self.auction.place_bid(self.maria, '15000')

        self.assertEqual(self.auction.current_price, Decimal('15000.00'))
        self.assertEqual(self.auction.current_leader, self.juan)

    def test_leader_can_raise_own_max_without_moving_the_price(self):
        self.auction.place_bid(self.juan, '15000')
        self.auction.place_bid(self.maria, '12000')
        price_before = self.auction.current_price

        self.auction.place_bid(self.juan, '30000')

        self.assertEqual(self.auction.current_price, price_before)
        self.assertEqual(self.auction.current_leader, self.juan)

    def test_leader_cannot_lower_own_max(self):
        self.auction.place_bid(self.juan, '15000')
        with self.assertRaises(BidError):
            self.auction.place_bid(self.juan, '15000')

    def test_seller_cannot_bid(self):
        with self.assertRaises(BidError):
            self.auction.place_bid(self.staff, '20000')

    def test_bid_on_scheduled_auction_is_rejected(self):
        self.auction.starts_at = timezone.now() + timedelta(days=1)
        self.auction.status = STATUS_SCHEDULED
        self.auction.save()

        with self.assertRaises(BidError):
            self.auction.place_bid(self.juan, '20000')

    def test_min_next_bid_tracks_the_increment(self):
        self.assertEqual(self.auction.min_next_bid, Decimal('10000.00'))
        self.auction.place_bid(self.juan, '15000')
        self.assertEqual(self.auction.min_next_bid, Decimal('10500.00'))


class AntiSnipeTestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="platform", password="pw", is_staff=True)
        self.juan = User.objects.create_user(username="juan", password="pw")
        self.card = make_card()

    def _auction(self, ends_in):
        return Auction.objects.create(
            card=self.card, seller=self.staff,
            starting_price=Decimal('1000.00'), min_increment=Decimal('500.00'),
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() + ends_in,
            status=STATUS_LIVE,
        )

    def test_late_bid_pushes_the_close_back(self):
        auction = self._auction(timedelta(minutes=1))
        original_end = auction.ends_at

        auction.place_bid(self.juan, '2000')

        self.assertGreater(auction.ends_at, original_end)
        self.assertAlmostEqual(auction.seconds_left, ANTI_SNIPE_WINDOW.total_seconds(), delta=5)

    def test_early_bid_leaves_the_close_alone(self):
        auction = self._auction(timedelta(days=2))
        original_end = auction.ends_at

        auction.place_bid(self.juan, '2000')

        self.assertEqual(auction.ends_at, original_end)


class AuctionSettlementTestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="platform", password="pw", is_staff=True)
        self.juan = User.objects.create_user(username="juan", password="pw")
        self.card = make_card()

    def _live_auction(self, **kwargs):
        defaults = dict(
            card=self.card, seller=self.staff,
            starting_price=Decimal('10000.00'), min_increment=Decimal('500.00'),
            starts_at=timezone.now() - timedelta(days=7),
            ends_at=timezone.now() + timedelta(minutes=30),
            status=STATUS_LIVE,
        )
        defaults.update(kwargs)
        return Auction.objects.create(**defaults)

    def _expire(self, auction):
        Auction.objects.filter(pk=auction.pk).update(ends_at=timezone.now() - timedelta(seconds=1))
        auction.refresh_from_db()

    def test_settling_names_a_winner_and_opens_a_cart(self):
        auction = self._live_auction()
        auction.place_bid(self.juan, '20000')
        self._expire(auction)

        auction.settle()

        self.assertEqual(auction.status, STATUS_CLOSED)
        self.assertEqual(auction.winner, self.juan)
        self.assertEqual(auction.winning_amount, Decimal('10000.00'))
        self.assertIsNotNone(auction.cart)
        self.assertEqual(auction.cart.source, Cart.SOURCE_AUCTION)
        self.assertEqual(auction.cart.buyer, self.juan)

        item = auction.cart.items.get()
        self.assertEqual(item.card, self.card)
        self.assertEqual(item.price_ars, Decimal('10000.00'))
        # The winner arrives to a chat that already explains the win.
        self.assertEqual(auction.cart.messages.count(), 1)

    def test_no_bids_closes_without_a_winner_or_cart(self):
        auction = self._live_auction()
        self._expire(auction)

        auction.settle()

        self.assertEqual(auction.status, STATUS_CLOSED)
        self.assertIsNone(auction.winner)
        self.assertIsNone(auction.cart)

    def test_unmet_reserve_closes_without_a_winner(self):
        auction = self._live_auction(reserve_price=Decimal('50000.00'))
        auction.place_bid(self.juan, '20000')
        self._expire(auction)

        auction.settle()

        self.assertEqual(auction.status, STATUS_CLOSED)
        self.assertIsNone(auction.winner)
        self.assertIsNone(auction.cart)

    def test_settle_is_idempotent(self):
        auction = self._live_auction()
        auction.place_bid(self.juan, '20000')
        self._expire(auction)

        auction.settle()
        cart_id = auction.cart_id
        auction.settle()

        self.assertEqual(auction.cart_id, cart_id)
        self.assertEqual(Cart.objects.count(), 1)

    def test_settle_due_auctions_opens_and_closes(self):
        upcoming = self._live_auction(
            starts_at=timezone.now() - timedelta(minutes=1),
            ends_at=timezone.now() + timedelta(days=1),
            status=STATUS_SCHEDULED,
        )
        finished = self._live_auction()
        self._expire(finished)

        opened, closed = settle_due_auctions()

        upcoming.refresh_from_db()
        finished.refresh_from_db()
        self.assertEqual((opened, closed), (1, 1))
        self.assertEqual(upcoming.status, STATUS_LIVE)
        self.assertEqual(finished.status, STATUS_CLOSED)

    def test_expired_auction_settles_on_read(self):
        auction = self._live_auction()
        auction.place_bid(self.juan, '20000')
        self._expire(auction)

        response = self.client.get(reverse('auctions:auctions-detail', args=[auction.pk]))

        self.assertEqual(response.data['status'], STATUS_CLOSED)
        self.assertEqual(response.data['winner'], 'juan')


class AuctionAPITestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="platform", password="pw", is_staff=True)
        self.juan = User.objects.create_user(username="juan", password="pw")
        self.maria = User.objects.create_user(username="maria", password="pw")
        self.card = make_card()
        self.auction = Auction.objects.create(
            card=self.card, seller=self.staff,
            starting_price=Decimal('10000.00'), min_increment=Decimal('500.00'),
            reserve_price=Decimal('12000.00'),
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(days=7),
            status=STATUS_LIVE,
        )

    def test_list_is_public(self):
        response = self.client.get(reverse('auctions:auctions-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_creating_requires_staff(self):
        self.client.force_authenticate(user=self.juan)
        response = self.client.post(reverse('auctions:auctions-list'), {
            'card_id': self.card.id,
            'starting_price': '5000',
            'starts_at': timezone.now().isoformat(),
            'ends_at': (timezone.now() + timedelta(days=7)).isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_creates_auction_from_an_existing_card(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(reverse('auctions:auctions-list'), {
            'card_id': self.card.id,
            'starting_price': '5000',
            'min_increment': '250',
            'starts_at': timezone.now().isoformat(),
            'ends_at': (timezone.now() + timedelta(days=7)).isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['seller'], 'platform')
        self.assertEqual(Auction.objects.count(), 2)

    def test_created_auction_that_already_opened_comes_back_live(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(reverse('auctions:auctions-list'), {
            'card_id': self.card.id,
            'starting_price': '5000',
            'starts_at': (timezone.now() - timedelta(minutes=1)).isoformat(),
            'ends_at': (timezone.now() + timedelta(days=7)).isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], STATUS_LIVE)

    def test_create_rejects_close_before_open(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(reverse('auctions:auctions-list'), {
            'card_id': self.card.id,
            'starting_price': '5000',
            'starts_at': timezone.now().isoformat(),
            'ends_at': (timezone.now() - timedelta(days=1)).isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bidding_requires_auth(self):
        response = self.client.post(
            reverse('auctions:auctions-bid', args=[self.auction.pk]),
            {'max_amount': '20000'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bid_endpoint_returns_updated_auction(self):
        self.client.force_authenticate(user=self.juan)
        response = self.client.post(
            reverse('auctions:auctions-bid', args=[self.auction.pk]),
            {'max_amount': '20000'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['current_price'], '10000.00')
        self.assertEqual(response.data['current_leader'], 'juan')
        self.assertTrue(response.data['is_leading'])
        self.assertEqual(response.data['my_max_bid'], '20000.00')

    def test_bid_error_is_a_400_with_a_message(self):
        self.client.force_authenticate(user=self.juan)
        response = self.client.post(
            reverse('auctions:auctions-bid', args=[self.auction.pk]),
            {'max_amount': '1'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_hidden_ceiling_never_leaks(self):
        self.auction.place_bid(self.juan, '99999')
        self.client.force_authenticate(user=self.maria)

        detail = self.client.get(reverse('auctions:auctions-detail', args=[self.auction.pk]))
        history = self.client.get(reverse('auctions:auctions-bids', args=[self.auction.pk]))

        self.assertNotIn('leader_max_amount', detail.data)
        self.assertIsNone(detail.data['my_max_bid'])
        self.assertNotIn('max_amount', history.data[0])

    def test_reserve_amount_is_staff_only(self):
        url = reverse('auctions:auctions-detail', args=[self.auction.pk])

        self.client.force_authenticate(user=self.juan)
        as_bidder = self.client.get(url)
        self.client.force_authenticate(user=self.staff)
        as_staff = self.client.get(url)

        self.assertTrue(as_bidder.data['has_reserve'])
        self.assertIsNone(as_bidder.data['reserve_price'])
        self.assertEqual(as_staff.data['reserve_price'], '12000.00')

    def test_editing_an_auction_with_bids_is_blocked(self):
        self.auction.place_bid(self.juan, '20000')
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            reverse('auctions:auctions-detail', args=[self.auction.pk]),
            {'starting_price': '1'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_staff_can_force_close(self):
        self.auction.place_bid(self.juan, '20000')
        self.auction.place_bid(self.maria, '12000')  # clears the $12.000 reserve
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(reverse('auctions:auctions-close', args=[self.auction.pk]))

        self.assertEqual(response.data['status'], STATUS_CLOSED)
        self.assertEqual(response.data['winner'], 'juan')
        self.assertEqual(response.data['winning_amount'], '12500.00')

    def test_force_close_below_reserve_leaves_no_winner(self):
        self.auction.place_bid(self.juan, '20000')
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(reverse('auctions:auctions-close', args=[self.auction.pk]))

        self.assertEqual(response.data['status'], STATUS_CLOSED)
        self.assertIsNone(response.data['winner'])
        self.assertFalse(response.data['reserve_met'])

    def test_cancelled_auction_takes_no_bids(self):
        self.auction.cancel()
        self.client.force_authenticate(user=self.juan)

        response = self.client.post(
            reverse('auctions:auctions-bid', args=[self.auction.pk]),
            {'max_amount': '20000'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mine_filter_returns_only_auctions_i_bid_on(self):
        self.auction.place_bid(self.juan, '20000')
        other = Auction.objects.create(
            card=make_card('c2', 'Mox Ruby'), seller=self.staff,
            starting_price=Decimal('1000.00'),
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(days=7),
            status=STATUS_LIVE,
        )
        self.client.force_authenticate(user=self.juan)

        response = self.client.get(reverse('auctions:auctions-list'), {'mine': '1'})

        ids = [a['id'] for a in response.data]
        self.assertIn(self.auction.pk, ids)
        self.assertNotIn(other.pk, ids)


class DefaultWindowTestCase(APITestCase):
    def test_window_opens_on_a_friday_and_runs_a_week(self):
        starts_at, ends_at = default_auction_window()

        self.assertEqual(starts_at.astimezone(timezone.get_fixed_timezone(-180)).weekday(), 4)
        self.assertEqual(ends_at - starts_at, timedelta(days=7))
        self.assertGreater(starts_at, timezone.now())

    def test_endpoint_is_staff_only(self):
        url = reverse('auctions:auctions-default-window')

        anonymous = self.client.get(url)
        self.client.force_authenticate(user=User.objects.create_user(username="s", password="pw", is_staff=True))
        as_staff = self.client.get(url)

        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(as_staff.status_code, status.HTTP_200_OK)
        self.assertIn('starts_at', as_staff.data)
