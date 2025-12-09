from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsOwnerOrReadOnly, IsSupportOrOwner
from .models import Ad, Proposal
from .serializers import AdSerializer, ProposalSerializer
from .serializers import CommentSerializer
from .models import Comment
from .serializers import RatingSerializer
from .models import Rating
from .models import Ticket
from .serializers import TicketSerializer


class AdListCreateView(generics.ListCreateAPIView):
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer

    def perform_create(self, serializer):
        # Only customers can create ads
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'customer':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only customers can create ads')
        serializer.save(creator=self.request.user)


class AdDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class ProposalListCreateView(generics.ListCreateAPIView):
    queryset = Proposal.objects.all().order_by('-created_at')
    serializer_class = ProposalSerializer

    def perform_create(self, serializer):
        # Only contractors can create proposals
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'contractor':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only contractors can create proposals')
        serializer.save(contractor=self.request.user)
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Proposal.objects.none()
        if getattr(user, 'role', None) == 'contractor':
            return Proposal.objects.filter(contractor=user).order_by('-created_at')
        if getattr(user, 'role', None) == 'customer':
            # show proposals for ads created by this customer
            return Proposal.objects.filter(ad__creator=user).order_by('-created_at')
        # support or admin or other roles see all
        return Proposal.objects.all().order_by('-created_at')


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


class AdCommentsListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        ad_id = self.kwargs.get('ad_id')
        return Comment.objects.filter(ad_id=ad_id).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer

    def get_queryset(self):
        contractor_id = self.kwargs.get('contractor_id')
        if contractor_id:
            return Rating.objects.filter(contractor_id=contractor_id).order_by('-created_at')
        return Rating.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        # Only customers should be able to rate
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'customer':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only customers can rate contractors')
        # Ensure contractor is a user with contractor role
        contractor_id = self.request.data.get('contractor')
        if not contractor_id:
            raise serializers.ValidationError({'contractor': 'This field is required.'})
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            contractor = User.objects.get(pk=contractor_id)
        except User.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Contractor not found')
        if contractor.role != 'contractor':
            from rest_framework.exceptions import ValidationError
            raise ValidationError('You can only rate contractors')
        serializer.save(rater=self.request.user, contractor=contractor)


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSupportOrOwner]
    
    def perform_update(self, serializer):
        # Only support users may set assignee or close the ticket; owner can update title/description
        assignee_id = self.request.data.get('assignee')
        if assignee_id:
            # Only support role can assign
            if getattr(self.request.user, 'role', None) != 'support':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Only support users can assign tickets')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(pk=assignee_id)
            except User.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound('Assignee not found')
            serializer.save(assignee=user)
            return
        serializer.save()
