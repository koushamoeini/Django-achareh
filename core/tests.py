from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User
from .models import Ad


class AdAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_ad(self):
        url = reverse('ad-list-create')
        data = {'title': 'Test Ad', 'description': 'Test description'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Ad.objects.count(), 1)
        ad = Ad.objects.first()
        self.assertEqual(ad.title, 'Test Ad')
        self.assertEqual(ad.creator, self.user)
