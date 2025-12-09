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
        ldata = lresp.data.get('results', lresp.data)
        self.assertEqual(len(ldata), 1)
        # customer should see both proposals for his ad
        self.client.force_authenticate(user=customer)
        lresp2 = self.client.get(reverse('proposal-list-create'))
        self.assertEqual(lresp2.status_code, 200)
        ldata2 = lresp2.data.get('results', lresp2.data)
        self.assertEqual(len(ldata2), 2)

    def test_proposal_complete_and_confirm(self):
        # Set up customer, contractor, ad, proposal
        customer = User.objects.create_user(username='ccomp', password='p', role='customer')
        contractor = User.objects.create_user(username='contcomp', password='p', role='contractor')
        self.client.force_authenticate(user=customer)
        ad_resp = self.client.post(reverse('ad-list-create'), {'title': 'ToComplete', 'description': 'desc'}, format='json')
        ad_id = ad_resp.data['id']
        self.client.force_authenticate(user=contractor)
        prop_resp = self.client.post(reverse('proposal-list-create'), {'ad': ad_id, 'price': '40'}, format='json')
        prop_id = prop_resp.data['id']
        # Customer accepts proposal
        self.client.force_authenticate(user=customer)
        resp_accept = self.client.post(reverse('proposal-accept', kwargs={'pk': prop_id}), format='json')
        self.assertEqual(resp_accept.status_code, 200)
        # Contractor marks completed
        self.client.force_authenticate(user=contractor)
        resp_complete = self.client.post(reverse('proposal-complete', kwargs={'pk': prop_id}), format='json')
        self.assertEqual(resp_complete.status_code, 200)
        # Customer confirms completion
        self.client.force_authenticate(user=customer)
        resp_confirm = self.client.post(reverse('proposal-confirm', kwargs={'pk': prop_id}), format='json')
        self.assertEqual(resp_confirm.status_code, 200)
        from core.models import Proposal, Ad
        prop = Proposal.objects.get(pk=prop_id)
        ad = Ad.objects.get(pk=ad_id)
        self.assertTrue(prop.completed)
        self.assertEqual(ad.status, 'done')

    def test_ratings_filters_and_contractor_profile(self):
        # Create contractor and several ratings to check filters and profile
        contractor = User.objects.create_user(username='ratetest', password='p', role='contractor')
        customer1 = User.objects.create_user(username='c1', password='p', role='customer')
        customer2 = User.objects.create_user(username='c2', password='p', role='customer')
        self.client.force_authenticate(user=customer1)
        r1 = self.client.post(reverse('ratings-list-create'), {'contractor': contractor.id, 'score': 5, 'comment': 'Great'}, format='json')
        self.assertEqual(r1.status_code, 201)
        self.client.force_authenticate(user=customer2)
        r2 = self.client.post(reverse('ratings-list-create'), {'contractor': contractor.id, 'score': 3, 'comment': 'Good'}, format='json')
        self.assertEqual(r2.status_code, 201)
        # filter ratings by min_score
        gresp = self.client.get(reverse('contractor-ratings-list-create', kwargs={'contractor_id': contractor.id}) + '?min_score=4')
        self.assertEqual(gresp.status_code, 200)
        gresults = gresp.data.get('results', gresp.data)
        self.assertEqual(len(gresults), 1)
        # check contractor profile avg & count
        profile_resp = self.client.get(reverse('contractor-profile', kwargs={'pk': contractor.id}))
        self.assertEqual(profile_resp.status_code, 200)
        self.assertEqual(profile_resp.data['ratings_count'], 2)
        self.assertAlmostEqual(profile_resp.data['avg_rating'], 4.0)

    def test_contractor_list_filter_and_order(self):
        cont1 = User.objects.create_user(username='cl1', password='p', role='contractor')
        cont2 = User.objects.create_user(username='cl2', password='p', role='contractor')
        cust = User.objects.create_user(username='clcust', password='p', role='customer')
        # give cont1 three 5-star ratings; cont2 one 4-star
        self.client.force_authenticate(user=cust)
        self.client.post(reverse('ratings-list-create'), {'contractor': cont1.id, 'score': 5}, format='json')
        self.client.post(reverse('ratings-list-create'), {'contractor': cont1.id, 'score': 5}, format='json')
        self.client.post(reverse('ratings-list-create'), {'contractor': cont1.id, 'score': 5}, format='json')
        self.client.post(reverse('ratings-list-create'), {'contractor': cont2.id, 'score': 4}, format='json')
        # list contractors ordered by avg_rating
        lresp = self.client.get(reverse('contractor-list') + '?order_by=avg_rating')
        self.assertEqual(lresp.status_code, 200)
        # first contractor should have higher avg rating
        lresults = lresp.data.get('results', lresp.data)
        self.assertEqual(lresults[0]['id'], cont1.id)
        # filter by min_reviews (cont1 has 3, cont2 has 1)
        mresp = self.client.get(reverse('contractor-list') + '?min_reviews=2')
        mresults = mresp.data.get('results', mresp.data)
        self.assertEqual(len(mresults), 1)

    def test_admin_can_change_user_role(self):
        admin = User.objects.create_superuser(username='super', password='sp', email='s@example.com')
        target = User.objects.create_user(username='tuser', password='t', role='customer')
        self.client.force_authenticate(user=admin)
        resp = self.client.patch(reverse('user-role-update', kwargs={'pk': target.id}), {'role': 'contractor'}, format='json')
        self.assertEqual(resp.status_code, 200)
        target.refresh_from_db()
        self.assertEqual(target.role, 'contractor')
        # non-admin cannot change
        other = User.objects.create_user(username='regular', password='p', role='customer')
        self.client.force_authenticate(user=other)
        resp2 = self.client.patch(reverse('user-role-update', kwargs={'pk': target.id}), {'role': 'customer'}, format='json')
        self.assertEqual(resp2.status_code, 403)

    def test_filter_ads_by_status_and_title(self):
        cust = User.objects.create_user(username='custfilter', password='p', role='customer')
        self.client.force_authenticate(user=cust)
        self.client.post(reverse('ad-list-create'), {'title': 'FilterMe', 'description': 'd', 'status': 'open'}, format='json')
        self.client.post(reverse('ad-list-create'), {'title': 'Other', 'description': 'd', 'status': 'done'}, format='json')
        resp = self.client.get(reverse('ad-list-create') + '?status=open')
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get('results', resp.data)
        self.assertEqual(len(results), 1)
        resp2 = self.client.get(reverse('ad-list-create') + '?title=FilterMe')
        results2 = resp2.data.get('results', resp2.data)
        self.assertEqual(len(results2), 1)

    def test_ad_detail_nested_proposals_and_comments(self):
        # Setup ad, proposal and comment
        customer = User.objects.create_user(username='nested_cust', password='p', role='customer')
        contractor = User.objects.create_user(username='nested_cont', password='p', role='contractor')
        self.client.force_authenticate(user=customer)
        ad_resp = self.client.post(reverse('ad-list-create'), {'title': 'Nested', 'description': 'desc'}, format='json')
        ad_id = ad_resp.data['id']
        self.client.force_authenticate(user=contractor)
        self.client.post(reverse('proposal-list-create'), {'ad': ad_id, 'price': '50', 'message': 'I can do'}, format='json')
        # add comment
        self.client.force_authenticate(user=contractor)
        self.client.post(reverse('ad-comments-list-create', kwargs={'ad_id': ad_id}), {'ad': ad_id, 'text': 'Hello'}, format='json')
        # fetch ad detail
        self.client.force_authenticate(user=customer)
        get_resp = self.client.get(reverse('ad-detail', kwargs={'pk': ad_id}))
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn('proposals', get_resp.data)
        self.assertIn('comments', get_resp.data)
        self.assertGreaterEqual(len(get_resp.data['proposals']), 1)
        self.assertGreaterEqual(len(get_resp.data['comments']), 1)

    def test_contractor_schedule_create_and_view(self):
        # Create contractor and schedule
        contractor = User.objects.create_user(username='cont_sched', password='p', role='contractor')
        self.client.force_authenticate(user=contractor)
        resp = self.client.post(reverse('contractor-schedule-list-create', kwargs={'contractor_id': contractor.id}), {'day_of_week': 0, 'start_time': '09:00:00', 'end_time': '12:00:00', 'is_available': True, 'location': 'Tehran'}, format='json')
        # contractor should be able to create schedule
        self.assertEqual(resp.status_code, 201)
        sid = resp.data['id']
        # a customer can view contractor schedule
        customer = User.objects.create_user(username='cust_view', password='p', role='customer')
        self.client.force_authenticate(user=customer)
        vresp = self.client.get(reverse('contractor-schedule-list-create', kwargs={'contractor_id': contractor.id}))
        self.assertEqual(vresp.status_code, 200)
        self.assertGreaterEqual(len(vresp.data), 1)
        # non-contractor cannot create schedule
        self.client.force_authenticate(user=customer)
        resp2 = self.client.post(reverse('contractor-schedule-list-create', kwargs={'contractor_id': contractor.id}), {'day_of_week': 1, 'start_time': '13:00:00', 'end_time': '16:00:00'}, format='json')
        self.assertEqual(resp2.status_code, 403)

    def test_ads_pagination(self):
        # Create 15 ads and check pagination
        cust = User.objects.create_user(username='pagcust', password='p', role='customer')
        self.client.force_authenticate(user=cust)
        for i in range(15):
            self.client.post(reverse('ad-list-create'), {'title': f'PAd {i}', 'description': 'd'}, format='json')
        resp = self.client.get(reverse('ad-list-create'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 15)
        self.assertEqual(len(resp.data['results']), 10)
        resp2 = self.client.get(reverse('ad-list-create') + '?page=2')
        self.assertEqual(len(resp2.data['results']), 5)

    def test_contractor_list_pagination(self):
        # create 12 contractors and check contractor list is paginated
        cust = User.objects.create_user(username='custpage', password='p', role='customer')
        contractors = []
        for i in range(12):
            contractors.append(User.objects.create_user(username=f'contpag{i}', password='p', role='contractor'))
        # a customer rates some contractors to provide data
        self.client.force_authenticate(user=cust)
        for idx, cont in enumerate(contractors):
            if idx % 2 == 0:
                self.client.post(reverse('ratings-list-create'), {'contractor': cont.id, 'score': 5}, format='json')
        lresp = self.client.get(reverse('contractor-list'))
        self.assertEqual(lresp.status_code, 200)
        self.assertEqual(lresp.data['count'], 12)
        self.assertEqual(len(lresp.data['results']), 10)
        p2 = self.client.get(reverse('contractor-list') + '?page=2')
        self.assertEqual(len(p2.data['results']), 2)

    
