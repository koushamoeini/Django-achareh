from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Ad, Proposal, Comment, Rating, Ticket, Schedule


class Command(BaseCommand):
    help = "Seed the database with example users, ads, proposals, comments, ratings, tickets, and schedules."

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

        contractor, _ = User.objects.get_or_create(
            username='demo_contractor',
            defaults={
                'email': 'contractor@example.com',
                'role': 'contractor',
            },
        )
        contractor.set_password('DemoPass123')
        contractor.save()

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
        if created:
            admin.set_password('DemoPass123')
            admin.save()
        elif not admin.has_usable_password():
            admin.set_password('DemoPass123')
            admin.save()

        self.stdout.write("Creating example ad, proposals, comments, and rating...")
        ad, _ = Ad.objects.get_or_create(
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
        proposal, _ = Proposal.objects.get_or_create(
            ad=ad,
            contractor=contractor,
            defaults={'price': '1450.00', 'message': 'Available next week.', 'accepted': True},
        )
        Comment.objects.get_or_create(
            ad=ad,
            author=contractor,
            defaults={'text': 'I can start on Monday and finish in 5 days.'},
        )
        Rating.objects.get_or_create(
            contractor=contractor,
            rater=customer,
            defaults={'score': 5, 'comment': 'Great communication.'},
        )

        self.stdout.write("Creating sample ticket and schedule...")
        Ticket.objects.get_or_create(
            title='Billing question',
            defaults={
                'description': 'Need clarification on payment schedule.',
                'creator': customer,
                'status': 'open',
            },
        )
        Schedule.objects.get_or_create(
            contractor=contractor,
            day_of_week=0,
            start_time='09:00:00',
            end_time='14:00:00',
            defaults={'location': 'Tehran', 'is_available': True},
        )

        self.stdout.write(self.style.SUCCESS('Seed data creation completed.'))
