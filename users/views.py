from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import LoginRequestSerializer, UserSerializer
from .models import User


@extend_schema(
    summary='Register a user',
    examples=[
        OpenApiExample(
            'Register customer',
            value={
                'username': 'demo_new_customer',
                'email': 'demo_new_customer@example.com',
                'phone_number': '+989111111111',
                'role': 'customer',
                'password': 'Pass12345'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Register contractor',
            value={
                'username': 'demo_new_contractor',
                'email': 'demo_new_contractor@example.com',
                'phone_number': '+989222222222',
                'role': 'contractor',
                'password': 'Pass12345'
            },
            request_only=True,
        ),
    ],
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    summary='Login with username/email/phone',
    request=LoginRequestSerializer,
    examples=[
        OpenApiExample(
            'Login with username',
            value={
                'username': 'demo_customer',
                'password': 'DemoPass123',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Login with email',
            value={
                'email': 'customer@example.com',
                'password': 'DemoPass123'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Login with phone',
            value={
                'phone_number': '+989111000001',
                'password': 'DemoPass123'
            },
            request_only=True,
        ),
    ],
)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        password = data.get('password')
        identifier = (
            data.get('username')
            or data.get('email')
            or data.get('phone_number')
        )
        if not identifier or not password:
            return Response(
                {
                    'detail': 'username/email/phone and password are required for login.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(
            Q(username=identifier) | Q(email=identifier) | Q(phone_number=identifier)
        ).first()
        if not user or not user.check_password(password):
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
