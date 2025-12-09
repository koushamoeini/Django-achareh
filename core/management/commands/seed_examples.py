from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

from core.models import Ad, Proposal, Comment, Rating, Ticket, Schedule


class Command(BaseCommand):
    help = "Seed the database with comprehensive example data covering all main features."

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write("Creating demo users...")
        customer, _ = User.objects.get_or_create(
            username='demo_customer',
            defaults={
                'email': 'customer@example.com',
                'role': 'customer',
            },
        )
        customer.set_password('DemoPass123')
        customer.save()

        customer2, _ = User.objects.get_or_create(
            username='demo_customer2',
            defaults={
                'email': 'customer2@example.com',
                'role': 'customer',
            },
        )
        customer2.set_password('DemoPass123')
        customer2.save()

        contractor, _ = User.objects.get_or_create(
            username='demo_contractor',
            defaults={
                'email': 'contractor@example.com',
                'role': 'contractor',
            },
        )
        contractor.set_password('DemoPass123')
        contractor.save()

        contractor2, _ = User.objects.get_or_create(
            username='demo_contractor2',
            defaults={
                'email': 'contractor2@example.com',
                'role': 'contractor',
            },
        )
        contractor2.set_password('DemoPass123')
        contractor2.save()

        support, _ = User.objects.get_or_create(
            username='demo_support',
            defaults={
                'email': 'support@example.com',
                'role': 'support',
            },
        )
        support.set_password('DemoPass123')
        support.save()

        admin, created = User.objects.get_or_create(
            username='demo_admin',
            defaults={'email': 'admin@example.com', 'role': 'admin', 'is_superuser': True, 'is_staff': True},
        )
        admin.role = 'admin'
        admin.is_superuser = True
        admin.is_staff = True
        admin.set_password('DemoPass123')
        admin.save()

        self.stdout.write("Creating example ads, proposals, comments, ratings...")

        # Open ad (no accepted proposal)
        ad_open, _ = Ad.objects.get_or_create(
            title='Paint the villa',
            defaults={
                'description': 'Need a contractor to repaint the villa in Tehran.',
                'creator': customer,
                'status': 'open',
                'budget': '1500.00',
                'location': 'Tehran',
                'category': 'painting',
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + timezone.timedelta(days=14)).date(),
                'hours_per_day': '6.0',
            },
        )

        # Assigned ad (proposal accepted)
        ad_assigned, _ = Ad.objects.get_or_create(
            title='Kitchen remodel',
            defaults={
                'description': 'Remodel kitchen cabinets and counters.',
                'creator': customer,
                'status': 'assigned',
                'budget': '4000.00',
                'location': 'Isfahan',
                'category': 'carpentry',
                'start_date': (timezone.now() + timezone.timedelta(days=7)).date(),
                'end_date': (timezone.now() + timezone.timedelta(days=21)).date(),
                'hours_per_day': '8.0',
            },
        )

        prop_assigned, _ = Proposal.objects.get_or_create(
            ad=ad_assigned,
            contractor=contractor,
            defaults={'price': '3800.00', 'message': 'We can start in one week.', 'accepted': True},
        )
        # ensure ad status
        if not ad_assigned.status == 'assigned':
            ad_assigned.status = 'assigned'
            ad_assigned.save()

        # Done ad (proposal completed and confirmed)
        ad_done, _ = Ad.objects.get_or_create(
            title='Bathroom tiling',
            defaults={
                'description': 'Replace tiles and grout in bathroom.',
                'creator': customer2,
                'status': 'done',
                'budget': '1200.00',
                'location': 'Shiraz',
                'category': 'tiling',
                'start_date': (timezone.now() - timezone.timedelta(days=30)).date(),
                'end_date': (timezone.now() - timezone.timedelta(days=15)).date(),
                'hours_per_day': '5.0',
            },
        )

        prop_done, _ = Proposal.objects.get_or_create(
            ad=ad_done,
            contractor=contractor2,
            defaults={'price': '1100.00', 'message': 'Finished last month.', 'accepted': True, 'completed': True},
        )
        if not ad_done.status == 'done':
            ad_done.status = 'done'
            ad_done.save()

        # Additional proposals on open ad
        Proposal.objects.get_or_create(ad=ad_open, contractor=contractor, defaults={'price': '1450.00', 'message': 'Available next week.'})
        Proposal.objects.get_or_create(ad=ad_open, contractor=contractor2, defaults={'price': '1400.00', 'message': 'I can start tomorrow.'})

        # Comments
        Comment.objects.get_or_create(ad=ad_open, author=contractor, defaults={'text': 'I can start on Monday and finish in 5 days.'})
        Comment.objects.get_or_create(ad=ad_open, author=customer2, defaults={'text': 'Please share your portfolio.'})

        # Ratings (multiple to produce averages)
        Rating.objects.get_or_create(contractor=contractor, rater=customer, defaults={'score': 5, 'comment': 'Great communication.'})
        Rating.objects.get_or_create(contractor=contractor, rater=customer2, defaults={'score': 4, 'comment': 'Good work.'})
        Rating.objects.get_or_create(contractor=contractor2, rater=customer, defaults={'score': 5, 'comment': 'Excellent finish.'})

        self.stdout.write("Creating sample tickets and schedules...")

        # Tickets
        ticket1, _ = Ticket.objects.get_or_create(
            title='Billing question',
            defaults={
                'description': 'Need clarification on payment schedule.',
                'creator': customer,
                'status': 'open',
            },
        )
        # assign ticket to support
        ticket1.assignee = support
        ticket1.status = 'in_progress'
        ticket1.save()

        ticket2, _ = Ticket.objects.get_or_create(
            title='Ad modification request',
            defaults={
                'description': 'Change budget and add images.',
                'creator': customer2,
                'status': 'open',
            },
        )

        # Schedules for contractors (multiple days)
        Schedule.objects.get_or_create(
            contractor=contractor,
            day_of_week=0,
            defaults={
                'start_time': datetime.time(9, 0),
                'end_time': datetime.time(14, 0),
                'location': 'Tehran',
                'is_available': True,
            },
        )
        Schedule.objects.get_or_create(
            contractor=contractor,
            day_of_week=2,
            defaults={
                'start_time': datetime.time(13, 0),
                'end_time': datetime.time(18, 0),
                'location': 'Tehran',
                'is_available': True,
            },
        )
        Schedule.objects.get_or_create(
            contractor=contractor2,
            day_of_week=1,
            defaults={
                'start_time': datetime.time(8, 0),
                'end_time': datetime.time(12, 0),
                'location': 'Shiraz',
                'is_available': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('Comprehensive seed data creation completed.'))
