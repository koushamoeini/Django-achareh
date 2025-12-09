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
from .models import Schedule
from .serializers import ScheduleSerializer


class AdListCreateView(generics.ListCreateAPIView):
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer

    def perform_create(self, serializer):
        # Only customers can create ads
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'customer':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only customers can create ads')
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        title = self.request.query_params.get('title')
        if status_param:
            qs = qs.filter(status=status_param)
        if title:
            qs = qs.filter(title__icontains=title)
        return qs


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


class ProposalCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            proposal = Proposal.objects.get(pk=pk)
        except Proposal.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only contractor who made the proposal can mark it as completed
        if proposal.contractor != request.user:
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)

        if not proposal.accepted:
            return Response({'detail': 'Proposal is not accepted.'}, status=status.HTTP_400_BAD_REQUEST)

        proposal.completed = True
        proposal.save()
        return Response({'detail': 'Proposal marked as completed.'})


class ProposalConfirmCompletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            proposal = Proposal.objects.get(pk=pk)
        except Proposal.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        ad = proposal.ad
        # Only ad owner can confirm completion
        if ad.creator != request.user:
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)

        if not proposal.completed:
            return Response({'detail': 'Proposal is not marked as completed by contractor.'}, status=status.HTTP_400_BAD_REQUEST)

        # mark ad as done
        proposal.accepted = True
        ad.status = 'done'
        ad.save()
        proposal.save()
        return Response({'detail': 'Proposal confirmed. Ad marked as done.'})


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
        min_score = self.request.query_params.get('min_score')
        max_score = self.request.query_params.get('max_score')
        if contractor_id:
            qs = Rating.objects.filter(contractor_id=contractor_id).order_by('-created_at')
            if min_score:
                qs = qs.filter(score__gte=int(min_score))
            if max_score:
                qs = qs.filter(score__lte=int(max_score))
            return qs
        qs = Rating.objects.all().order_by('-created_at')
        if min_score:
            qs = qs.filter(score__gte=int(min_score))
        if max_score:
            qs = qs.filter(score__lte=int(max_score))
        return qs

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


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        contractor_id = self.kwargs.get('contractor_id')
        if contractor_id:
            return Schedule.objects.filter(contractor_id=contractor_id).order_by('day_of_week', 'start_time')
        return Schedule.objects.all().order_by('contractor__id', 'day_of_week')

    def perform_create(self, serializer):
        # Only contractors can create schedules for themselves
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'contractor':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only contractors can create schedules')
        serializer.save(contractor=self.request.user)


class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class ContractorProfileView(generics.RetrieveAPIView):
    serializer_class = None

    def get(self, request, pk):
        from django.contrib.auth import get_user_model
        from django.db.models import Avg, Count
        from .serializers import ContractorProfileSerializer
        User = get_user_model()
        try:
            user = User.objects.annotate(avg_rating=Avg('ratings_received__score'), ratings_count=Count('ratings_received')).get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContractorProfileSerializer(user)
        # inject the annotated fields into data
        data = serializer.data
        data['avg_rating'] = float(user.avg_rating) if user.avg_rating is not None else None
        data['ratings_count'] = user.ratings_count
        return Response(data)


class ContractorListView(generics.ListAPIView):
    serializer_class = None

    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.db.models import Avg, Count
        from .serializers import ContractorListSerializer
        User = get_user_model()
        qs = User.objects.filter(role='contractor').annotate(avg_rating=Avg('ratings_received__score'), ratings_count=Count('ratings_received'))
        min_avg = request.query_params.get('min_avg')
        min_reviews = request.query_params.get('min_reviews')
        order_by = request.query_params.get('order_by')
        if min_avg:
            qs = qs.filter(avg_rating__gte=float(min_avg))
        if min_reviews:
            qs = qs.filter(ratings_count__gte=int(min_reviews))
        if order_by in ('avg_rating', 'ratings_count'):
            qs = qs.order_by('-' + order_by)
        serializer = ContractorListSerializer(qs, many=True)
        return Response(serializer.data)


class UserRoleUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not request.user.is_superuser:
            return Response({'detail': 'Only admin can change roles.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        new_role = request.data.get('role')
        if new_role not in dict(getattr(User, 'ROLE_CHOICES', [])):
            # fallback: check if user has role attribute choices
            if not hasattr(user, 'role'):
                return Response({'detail': 'Role field not available for this user.'}, status=status.HTTP_400_BAD_REQUEST)
        user.role = new_role
        user.save()
        from users.serializers import UserSerializer
        return Response(UserSerializer(user).data)
