from django.urls import path
from .views import AdListCreateView, AdDetailView, ProposalListCreateView, ProposalAcceptView, AdCommentsListCreateView, CommentDetailView, RatingListCreateView, TicketListCreateView, TicketDetailView

urlpatterns = [
    path('ads/', AdListCreateView.as_view(), name='ad-list-create'),
    path('ads/<int:pk>/', AdDetailView.as_view(), name='ad-detail'),
    path('proposals/', ProposalListCreateView.as_view(), name='proposal-list-create'),
    path('proposals/<int:pk>/accept/', ProposalAcceptView.as_view(), name='proposal-accept'),
    path('ads/<int:ad_id>/comments/', AdCommentsListCreateView.as_view(), name='ad-comments-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('contractors/<int:contractor_id>/ratings/', RatingListCreateView.as_view(), name='contractor-ratings-list-create'),
    path('ratings/', RatingListCreateView.as_view(), name='ratings-list-create'),
    path('tickets/', TicketListCreateView.as_view(), name='tickets-list-create'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
]
