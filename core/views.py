from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsOwnerOrReadOnly
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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class ProposalListCreateView(generics.ListCreateAPIView):
    queryset = Proposal.objects.all().order_by('-created_at')
    serializer_class = ProposalSerializer

    def perform_create(self, serializer):
        serializer.save(contractor=self.request.user)


class ProposalAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            proposal = Proposal.objects.get(pk=pk)
        except Proposal.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        ad = proposal.ad
        if ad.creator != request.user:
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)

        # Accept the proposal
        proposal.accepted = True
        proposal.save()
        ad.status = 'assigned'
        ad.save()
        return Response({'detail': 'Proposal accepted.'})
