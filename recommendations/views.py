from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import StyleImage, RecommendationLog, Feedback
from .serializers import StyleImageSerializer, FeedbackSerializer, \
    RecommendationLogListSerializer, RecommendationLogDetailSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .tasks import process_style_image_segmentation  # <--- IMPORT THE TASK


class StyleImageViewSet(viewsets.ModelViewSet):
    """
    Endpoint for uploading a style image.
    The creation triggers the background segmentation process.
    """
    queryset = StyleImage.objects.all()
    serializer_class = StyleImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return StyleImage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # First, save the StyleImage instance to the database
        style_image = serializer.save(user=self.request.user)

        # --- TRIGGER THE BACKGROUND TASK ---
        # We pass the ID of the object, not the object itself, as it's better for serialization.
        gender = self.request.data.get('gender')
        process_style_image_segmentation.delay(style_image.styleImageId, gender)

        # The view's job is done. It returns immediately to the user.
        # The Celery worker will handle the rest.


class RecommendationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View a history of your recommendations."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecommendationLog.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return RecommendationLogListSerializer
        if self.action == 'retrieve':
            return RecommendationLogDetailSerializer
        return RecommendationLogDetailSerializer  # fallback if you add other actions


class FeedbackViewSet(viewsets.ModelViewSet):
    """Create and view feedback on recommendations."""
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user)
