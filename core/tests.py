from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User
from .models import Ad
from .models import Comment


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

    def test_user_can_comment_and_author_can_update(self):
        # Users can comment on ad
        customer = User.objects.create_user(username='cust3', password='cust3pass', role='customer')
        self.client.force_authenticate(user=customer)
        resp = self.client.post(reverse('ad-list-create'), {'title': 'Ad B', 'description': 'd'}, format='json')
        ad_id = resp.data['id']
        # another user comments
        commenter = User.objects.create_user(username='c', password='p', role='contractor')
        self.client.force_authenticate(user=commenter)
        resp2 = self.client.post(reverse('ad-comments-list-create', kwargs={'ad_id': ad_id}), {'ad': ad_id, 'text': 'Hello'}, format='json')
        self.assertEqual(resp2.status_code, 201)
        comment_id = resp2.data['id']
        # check that only author can update
        self.client.force_authenticate(user=customer)
        resp3 = self.client.patch(reverse('comment-detail', kwargs={'pk': comment_id}), {'text': 'Hacked'}, format='json')
        self.assertEqual(resp3.status_code, 403)
        self.client.force_authenticate(user=commenter)
        resp4 = self.client.patch(reverse('comment-detail', kwargs={'pk': comment_id}), {'text': 'Updated'}, format='json')
        self.assertEqual(resp4.status_code, 200)

    def test_customer_can_rate_contractor(self):
        customer = User.objects.create_user(username='ratecust', password='rcpass', role='customer')
        contractor = User.objects.create_user(username='ratecont', password='rtpass', role='contractor')
        self.client.force_authenticate(user=customer)
        resp = self.client.post(reverse('ratings-list-create'), {'contractor': contractor.id, 'score': 5, 'comment': 'Great job!'}, format='json')
        self.assertEqual(resp.status_code, 201)
        from core.models import Rating
        self.assertEqual(Rating.objects.filter(contractor=contractor).count(), 1)

    def test_non_customer_cannot_rate(self):
        contractor1 = User.objects.create_user(username='cont1', password='p', role='contractor')
        contractor2 = User.objects.create_user(username='cont2', password='p', role='contractor')
        self.client.force_authenticate(user=contractor1)
        resp = self.client.post(reverse('ratings-list-create'), {'contractor': contractor2.id, 'score': 4}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_ticket_create_and_assign(self):
        customer = User.objects.create_user(username='t_cust', password='t_p', role='customer')
        support = User.objects.create_user(username='support', password='sup', role='support')
        other = User.objects.create_user(username='other', password='o', role='customer')
        self.client.force_authenticate(user=customer)
        resp = self.client.post(reverse('tickets-list-create'), {'title': 'Help', 'description': 'Need help'}, format='json')
        self.assertEqual(resp.status_code, 201)
        ticket_id = resp.data['id']
        # Other user can't assign
        self.client.force_authenticate(user=other)
        resp2 = self.client.patch(reverse('ticket-detail', kwargs={'pk': ticket_id}), {'assignee': support.id}, format='json')
        self.assertEqual(resp2.status_code, 403)
        # Support can assign
        self.client.force_authenticate(user=support)
        resp3 = self.client.patch(reverse('ticket-detail', kwargs={'pk': ticket_id}), {'assignee': support.id}, format='json')
        self.assertEqual(resp3.status_code, 200)
        from core.models import Ticket
        ticket = Ticket.objects.get(pk=ticket_id)
        self.assertEqual(ticket.assignee, support)

    def test_proposal_list_filters(self):
        # Setup: create ad by customer and two proposals by two contractors
        customer = User.objects.create_user(username='pcust', password='p', role='customer')
        cont1 = User.objects.create_user(username='cont1', password='p', role='contractor')
        cont2 = User.objects.create_user(username='cont2', password='p', role='contractor')
        self.client.force_authenticate(user=customer)
        ad_resp = self.client.post(reverse('ad-list-create'), {'title': 'Ad X', 'description': 'desc'}, format='json')
        ad_id = ad_resp.data['id']
        # contractor 1 posts proposal
        self.client.force_authenticate(user=cont1)
        resp1 = self.client.post(reverse('proposal-list-create'), {'ad': ad_id, 'price': '10.00'}, format='json')
        self.assertEqual(resp1.status_code, 201)
        # contractor 2 posts proposal
        self.client.force_authenticate(user=cont2)
        resp2 = self.client.post(reverse('proposal-list-create'), {'ad': ad_id, 'price': '20.00'}, format='json')
        self.assertEqual(resp2.status_code, 201)
        # contractor1 should only see his proposal
        self.client.force_authenticate(user=cont1)
        lresp = self.client.get(reverse('proposal-list-create'))
        self.assertEqual(lresp.status_code, 200)
        self.assertEqual(len(lresp.data), 1)
        # customer should see both proposals for his ad
        self.client.force_authenticate(user=customer)
        lresp2 = self.client.get(reverse('proposal-list-create'))
        self.assertEqual(lresp2.status_code, 200)
        self.assertEqual(len(lresp2.data), 2)

    def test_filter_ads_by_status_and_title(self):
        cust = User.objects.create_user(username='custfilter', password='p', role='customer')
        self.client.force_authenticate(user=cust)
        self.client.post(reverse('ad-list-create'), {'title': 'FilterMe', 'description': 'd', 'status': 'open'}, format='json')
        self.client.post(reverse('ad-list-create'), {'title': 'Other', 'description': 'd', 'status': 'done'}, format='json')
        resp = self.client.get(reverse('ad-list-create') + '?status=open')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        resp2 = self.client.get(reverse('ad-list-create') + '?title=FilterMe')
        self.assertEqual(len(resp2.data), 1)

    
