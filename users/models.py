from django.db import models

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from pgvector.django import VectorField


class User(AbstractUser):
    # UUID is not needed as Django's User model uses an integer PK.
    # Sticking with the default is easier unless UUIDs are a hard requirement.
    # If so, you'd need a more complex custom user model setup.
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    avatar_url = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    # The diagram has checkPassword and updateProfile as methods,
    # which are already handled by Django's User model and APIs.

    # We remove 'username' to allow login with email, or keep it as is.
    # For email-only login:
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avg_style_vector = VectorField(dimensions=2048, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
