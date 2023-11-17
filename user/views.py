"""
View for the user API.
"""
from rest_framework.response import Response
from rest_framework import (
    status,
    generics
)
from rest_framework_simplejwt import authentication as authenticationJWT
from user.serializers import UserSerializer
from user.permissions import IsCreationOrIsAuthenticated 
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from core.models import LoginAttempt
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken  # Import AccessToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import PermissionDenied




class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer
    
    
    

class ManagerUserAPiView(generics.RetrieveUpdateAPIView):
    """Manage for the authenticated users"""
    serializer_class = UserSerializer
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsCreationOrIsAuthenticated]

    def get_object(self):
        """Retrive and return a user."""
        # validate_time = timezone.now() - self.request.user.
        if self.request.user.created_at + timedelta(minutes=5) <= timezone.now():
            return self.request.user
        else:
            raise PermissionDenied(detail="The user is still in analysis", code=status.HTTP_403_FORBIDDEN)
            

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to user"""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('cpf')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username or password cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ip = get_client_ip(request=request)
        
        # Check if the user is blocked due to failed attempts
        recent_failed_attempts = LoginAttempt.objects.filter(
            username=username,
            successful=False,
            timestamp__gte=timezone.now() - timedelta(minutes=10),
            ip=ip
        ).count()

        if recent_failed_attempts >= 3:
            last_failed_attempt = LoginAttempt.objects.filter(
                username=username,
                successful=False,
                ip=ip
            ).latest('timestamp')

            time_elapsed = timezone.now() - last_failed_attempt.timestamp
            if time_elapsed < timedelta(minutes=5):
                return Response(
                    {"error": "Too many login attempts. Try again later."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
        # Track login attempt
        LoginAttempt.objects.create(
            username=username,
            successful=False,
            ip=ip
        )

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"detail": "No active account found with the given credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # If authentication succeeds, update the login attempt
        LoginAttempt.objects.filter(
            username=username,
            successful=False,
            ip=ip
        ).update(successful=True)

        # Generate JWT token
        access_token = AccessToken.for_user(user)
        token_data = {
            "access": str(access_token),
        }
        return Response(token_data, status=status.HTTP_200_OK)