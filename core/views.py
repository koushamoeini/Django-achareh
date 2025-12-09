from rest_framework import generics, permissions
from .models import Ad, Proposal
from .serializers import AdSerializer, ProposalSerializer


class AdListCreateView(generics.ListCreateAPIView):
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class AdDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer


class ProposalListCreateView(generics.ListCreateAPIView):
    queryset = Proposal.objects.all().order_by('-created_at')
    serializer_class = ProposalSerializer

    def perform_create(self, serializer):
        serializer.save(contractor=self.request.user)
