import random

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from django.core.cache import cache

from .models import UserProfile
from .serializers import UserProfileSerializer


# We use a custom ViewSet because there's only ONE profile per user.
# A standard ModelViewSet for listing all profiles would be a security risk.
class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    A ViewSet for viewing and editing the profile of the currently authenticated user.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # The key is to fetch the profile associated with the request's user.
        # This also ensures users can only see/edit their own profile.
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    # We rename the 'retrieve' action to avoid URL needing a pk
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PasswordResetCodeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        cache.set(f"reset-code-{email}", code, timeout=10 * 60)  # 10 minutes

        # Send the code via email
        send_mail(
            "Your password reset code",
            f"Your reset code is: {code}",
            "no-reply@example.com",
            [email],
        )

        return Response({"detail": "Reset code sent"}, status=200)


class PasswordResetConfirmWithCode(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        cached_code = cache.get(f"reset-code-{email}")
        if not cached_code or cached_code != code:
            return Response({"error": "Invalid or expired code"}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            cache.delete(f"reset-code-{email}")
            return Response({"detail": "Password reset successful"}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
