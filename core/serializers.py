from rest_framework import serializers
from .models import Ad, Proposal
from users.serializers import UserSerializer
from .models import Comment
from .models import Rating, Ticket
from .models import Schedule
from django.db.models import Avg, Count


class AdSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    proposals = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = ['id', 'title', 'description', 'creator', 'created_at', 'status', 'budget', 'category', 'location', 'start_date', 'end_date', 'hours_per_day', 'proposals', 'comments']

    def get_proposals(self, obj) -> list:
        qs = obj.proposals.all().order_by('-created_at')
        return ProposalSerializer(qs, many=True).data

    def get_comments(self, obj) -> list:
        qs = obj.comments.all().order_by('-created_at')
        return CommentSerializer(qs, many=True).data


class ProposalSerializer(serializers.ModelSerializer):
    contractor = UserSerializer(read_only=True)

    class Meta:
        model = Proposal
        fields = ['id', 'ad', 'contractor', 'price', 'message', 'created_at', 'accepted', 'completed']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'ad', 'author', 'text', 'created_at']


class RatingSerializer(serializers.ModelSerializer):
    rater = UserSerializer(read_only=True)
    contractor = UserSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'contractor', 'rater', 'score', 'comment', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'title', 'description', 'creator', 'assignee', 'status', 'created_at', 'updated_at']


class ScheduleSerializer(serializers.ModelSerializer):
    contractor = UserSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'contractor', 'day_of_week', 'start_time', 'end_time', 'location', 'is_available']


class ContractorProfileSerializer(serializers.ModelSerializer):
    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    ads = serializers.SerializerMethodField()

    class Meta:
        from users.models import User
        model = User
        fields = ['id', 'username', 'email', 'role', 'avg_rating', 'ratings_count', 'ads']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # include avg and count if annotated in queryset
        return data

    def get_ads(self, obj) -> list:
        from .serializers import AdSerializer
        qs = obj.ads.all().order_by('-created_at')
        return AdSerializer(qs, many=True).data


class ContractorListSerializer(serializers.ModelSerializer):
    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)

    class Meta:
        from users.models import User
        model = User
        fields = ['id', 'username', 'email', 'avg_rating', 'ratings_count']


class ProposalActionSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True, help_text='Action result message')


class UserRoleUpdateSerializer(serializers.Serializer):
    role = serializers.CharField(help_text='New role for the user')
