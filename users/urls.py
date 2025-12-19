from django.urls import path
from .views import RegisterView, LoginView

urlpatterns = [
    path('login/', LoginView.as_view(), name='api_token_auth'),
    path('register/', RegisterView.as_view(), name='register'),
]
