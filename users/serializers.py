from djoser.serializers import UserSerializer as BaseUserSerializer
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ('fcm_token',)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # This field is not part of the model's validation, just for data transfer.
    # It won't be saved automatically; we'll handle it in the validate() method.
    fcm_token = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        # Call the parent's validate method to authenticate the user and generate tokens
        data = super().validate(attrs)

        fcm_token = self.initial_data.get('fcm_token')

        # self.user is available here because super().validate() has run successfully
        if fcm_token:
            self.user.fcm_token = fcm_token
            # We save the user object with the updated token.
            # Using update_fields is efficient as it only touches the specified field.
            self.user.save(update_fields=['fcm_token'])

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avg_style_vector', 'updated_at']


# We can extend Djoser's default UserSerializer to include the profile
class UserSerializer(BaseUserSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('profile',)
