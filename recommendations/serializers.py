from rest_framework import serializers

from products.serializers import ProductMiniSerializer
from .models import StyleImage, RecommendationLog, Feedback


class StyleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleImage
        fields = ['styleImageId', 'image_url', 'uploaded_at']
        read_only_fields = ['styleImageId', 'uploaded_at']


# list: no products, keep user id + style_image
class RecommendationLogListSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecommendationLog
        fields = ('logId', 'user', 'style_image', 'created_at')  # no products, keep style_image
        depth = 1


# detail: include products, hide style_image
class RecommendationLogDetailSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recommended_products = ProductMiniSerializer(many=True, read_only=True)

    class Meta:
        model = RecommendationLog
        fields = ('logId', 'user', 'recommended_products', 'created_at')  # no style_image


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    # accept a UUID in the incoming payload
    logId = serializers.PrimaryKeyRelatedField(
        source="log",  # tell DRF this populates the `log` FK
        queryset=RecommendationLog.objects.all(),
        write_only=True
    )
    log = RecommendationLogListSerializer(read_only=True)  # keep the nested read-only view

    class Meta:
        model = Feedback
        fields = ['feedbackId', 'logId', 'log', 'is_good', 'user']
        depth = 1

    def validate(self, attrs):
        user = self.context['request'].user
        log = attrs['log']  # `logId` has already been mapped to `log`
        if Feedback.objects.filter(user=user, log=log).exists():
            raise serializers.ValidationError(
                "You already gave feedback for this recommendation."
            )
        return attrs
