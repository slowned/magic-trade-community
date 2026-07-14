from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from binders.models import Binder
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
