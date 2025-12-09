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

    def test_owner_can_update_ad(self):
        url = reverse('ad-detail', kwargs={'pk': Ad.objects.create(title='X', description='Y', creator=self.user).pk})
        data = {'title': 'Updated Title', 'description': 'new description'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        ad = Ad.objects.get(pk=response.data['id'])
        self.assertEqual(ad.title, 'Updated Title')

    def test_non_owner_cannot_update_ad(self):
        ad = Ad.objects.create(title='Owner Ad', description='Owner desc', creator=self.user)
        other = User.objects.create_user(username='other', password='otherpass')
        self.client.force_authenticate(user=other)
        url = reverse('ad-detail', kwargs={'pk': ad.pk})
        response = self.client.patch(url, {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_contractor_cannot_create_ad(self):
        contractor = User.objects.create_user(username='contractor1', password='pass', role='contractor')
        self.client.force_authenticate(user=contractor)
        response = self.client.post(reverse('ad-list-create'), {'title': 'CAd', 'description': 'Cdesc'}, format='json')
        self.assertEqual(response.status_code, 403)


class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_and_login(self):
        # Register
        url = '/api/auth/register/'
        data = {'username': 'newuser', 'password': 'newpass', 'email': 'new@example.com', 'role': 'customer'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        # Login
        url_login = '/api/auth/login/'
        response = self.client.post(url_login, {'username': 'newuser', 'password': 'newpass'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_contractor_create_proposal_and_owner_accepts(self):
        # create users
        customer = User.objects.create_user(username='customer', password='custpass', role='customer')
        contractor = User.objects.create_user(username='contractor', password='contpass', role='contractor')
        # customer creates an ad
        self.client.force_authenticate(user=customer)
        resp = self.client.post(reverse('ad-list-create'), {'title': 'Ad A', 'description': 'desc'}, format='json')
        self.assertEqual(resp.status_code, 201)
        ad_id = resp.data['id']
        # contractor posts a proposal
        self.client.force_authenticate(user=contractor)
        resp2 = self.client.post(reverse('proposal-list-create'), {'ad': ad_id, 'price': '100.00', 'message': 'I can do it'}, format='json')
        self.assertEqual(resp2.status_code, 201)
        proposal_id = resp2.data['id']
        # customer accepts the proposal
        self.client.force_authenticate(user=customer)
        resp3 = self.client.post(f'/api/proposals/{proposal_id}/accept/', format='json')
        self.assertEqual(resp3.status_code, 200)
        # assert that proposal accepted and ad status assigned
        from core.models import Proposal, Ad
        proposal = Proposal.objects.get(pk=proposal_id)
        self.assertTrue(proposal.accepted)
        ad = Ad.objects.get(pk=ad_id)
        self.assertEqual(ad.status, 'assigned')

    def test_customer_cannot_create_proposal(self):
        customer = User.objects.create_user(username='cust2', password='cust2pass', role='customer')
        ad = Ad.objects.create(title='A', description='d', creator=customer)
        self.client.force_authenticate(user=customer)
        response = self.client.post(reverse('proposal-list-create'), {'ad': ad.id, 'price': '20.00'}, format='json')
        self.assertEqual(response.status_code, 403)

    
