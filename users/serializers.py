from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avg_style_vector', 'updated_at']

# We can extend Djoser's default UserSerializer to include the profile
class UserSerializer(BaseUserSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('profile',)