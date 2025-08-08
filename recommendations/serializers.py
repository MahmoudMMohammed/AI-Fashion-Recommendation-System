from rest_framework import serializers
from .models import StyleImage, RecommendationLog, Feedback

class StyleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleImage
        fields = ['styleImageId', 'image_url', 'uploaded_at']
        read_only_fields = ['styleImageId', 'uploaded_at']

class RecommendationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationLog
        fields = '__all__'
        depth = 1 # Nest products and other related fields

class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Feedback
        fields = ['feedbackId', 'log', 'is_good', 'user']