from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from binders.models import Binder
from cards.models import Card
from carts.models import Cart, CartItem, Order, Rating
from users.serializers import UserSerializer


class UserViewSetTestCase(APITestCase):
    def setUp(self):
        """
        Set up users and binders
        """
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        self.binder1 = Binder.objects.create(user=self.user1, name="Binder1")
        self.binder2 = Binder.objects.create(user=self.user1, name="Binder2")
        self.binder3 = Binder.objects.create(user=self.user2, name="Binder3")

    def test_create_user(self):
        """Test use create."""
        url = reverse('users:user-list')
        data = {
            'username': 'user3',
            'password': 'password123',
            'email': 'user3_email@email.com',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='user3').exists())

    def test_list_users_requires_auth(self):
        """Anonymous requests are rejected."""
        url = reverse('users:user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users(self):
        """Tests user list."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('users:user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_user_detail_with_binders(self):
        """Tests user detail with own binders."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('users:user-detail', args=[self.user1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data
        self.assertEqual(user_data['username'], self.user1.username)

        binder_names = [binder['name'] for binder in user_data['binders']]
        self.assertIn(self.binder1.name, binder_names)
        self.assertIn(self.binder2.name, binder_names)

        self.assertNotIn(self.binder3.name, binder_names)


class PublicProfileTestCase(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="seller", password="password123")
        self.buyer1 = User.objects.create_user(username="buyer1", password="password123")
        self.buyer2 = User.objects.create_user(username="buyer2", password="password123")
        self.card = Card.objects.create(
            id="1", name="Card One", set_name="Set", color_identity="R",
            uri="uri1", scryfall_uri="scryfall_uri1", image_uri="http://image1.com",
        )
        Binder.objects.create(user=self.seller, name="Public binder", is_public=True)
        Binder.objects.create(user=self.seller, name="Private binder", is_public=False)

    def _completed_sale(self, buyer, quantity, score=None, comment=''):
        cart = Cart.objects.create(buyer=buyer, seller=self.seller, is_finalized=True)
        CartItem.objects.create(cart=cart, card=self.card, quantity=quantity)
        order = Order.objects.create(cart=cart, shipping_method='door_to_door', status='completed')
        if score is not None:
            Rating.objects.create(order=order, rater=buyer, ratee=self.seller, score=score, comment=comment)
        return order

    def test_public_profile_is_accessible_without_auth(self):
        url = reverse('users:user-public-profile', kwargs={'username': 'seller'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_profile_stats(self):
        self._completed_sale(self.buyer1, quantity=3, score=10, comment='Excelente')
        self._completed_sale(self.buyer2, quantity=2, score=7)
        # Pending order should not count as a successful trade nor as cards sold
        cart = Cart.objects.create(buyer=self.buyer1, seller=self.seller, is_finalized=True)
        CartItem.objects.create(cart=cart, card=self.card, quantity=5)
        Order.objects.create(cart=cart, shipping_method='door_to_door', status='pending')

        url = reverse('users:user-public-profile', kwargs={'username': 'seller'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating_avg'], 8.5)
        self.assertEqual(response.data['rating_count'], 2)
        self.assertEqual(response.data['successful_trades'], 2)
        self.assertEqual(response.data['cards_sold'], 5)
        binder_names = [b['name'] for b in response.data['binders']]
        self.assertEqual(binder_names, ['Public binder'])
        self.assertEqual(len(response.data['recent_ratings']), 2)

    def test_public_profile_counts_purchases_as_successful_trades(self):
        self._completed_sale(self.buyer1, quantity=1, score=9)

        url = reverse('users:user-public-profile', kwargs={'username': 'buyer1'})
        response = self.client.get(url)

        self.assertEqual(response.data['successful_trades'], 1)
        self.assertEqual(response.data['cards_sold'], 0)
        self.assertIsNone(response.data['rating_avg'])

    def test_public_profile_unknown_user_404(self):
        url = reverse('users:user-public-profile', kwargs={'username': 'ghost'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
