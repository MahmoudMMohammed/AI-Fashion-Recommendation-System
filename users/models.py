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
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
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


class Notification(models.Model):
    # WHO + WHAT
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=40, default="recommendations_ready", db_index=True)
    title = models.CharField(max_length=120, default="New recommendations are ready")
    message = models.TextField(blank=True, default="")

    # PAYLOAD (keep it flexible)
    # e.g. {"product_ids": ["uuid1","uuid2",...], "scores": {"uuid1":0.87,...}, "model":"v3.2"}
    payload = models.JSONField(default=dict, blank=True)

    # UX / STATE
    action_url = models.URLField(blank=True, default="")  # optional deep-link to your page
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "created_at"]),
            models.Index(fields=["type"]),
        ]
