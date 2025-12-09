from rest_framework import serializers
from .models import Ad, Proposal
from users.serializers import UserSerializer
from .models import Comment
from .models import Rating


class AdSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Ad
        fields = ['id', 'title', 'description', 'creator', 'created_at', 'status']


class ProposalSerializer(serializers.ModelSerializer):
    contractor = UserSerializer(read_only=True)

    class Meta:
        model = Proposal
        fields = ['id', 'ad', 'contractor', 'price', 'message', 'created_at', 'accepted']


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
