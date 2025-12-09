from rest_framework import serializers
from .models import Ad, Proposal
from users.serializers import UserSerializer


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
