from django.urls import path
from .views import AdListCreateView, AdDetailView, ProposalListCreateView, ProposalAcceptView

urlpatterns = [
    path('ads/', AdListCreateView.as_view(), name='ad-list-create'),
    path('ads/<int:pk>/', AdDetailView.as_view(), name='ad-detail'),
    path('proposals/', ProposalListCreateView.as_view(), name='proposal-list-create'),
    path('proposals/<int:pk>/accept/', ProposalAcceptView.as_view(), name='proposal-accept'),
]
