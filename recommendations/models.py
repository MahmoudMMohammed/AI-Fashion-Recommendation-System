from django.db import models

import uuid
from django.db import models
from users.models import User
from products.models import Product, Category


class StyleImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="styleImageId")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    image_url = models.ImageField(upload_to='style_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ImageSegment(models.Model):  # Renamed for clarity from Image_Segments
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="segmentId")
    style_image = models.ForeignKey(StyleImage, on_delete=models.CASCADE, related_name='segments')
    # This refers to the segmented image (e.g., the cropped shirt)
    image_url = models.ImageField(upload_to='segments/')
    category_type = models.ForeignKey(Category, on_delete=models.PROTECT)


class StyleEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="embeddingId")
    # This can be linked to either a user's uploaded segment or a product's image
    segment = models.OneToOneField(ImageSegment, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    embeddings = models.JSONField()  # Store the list of decimals (vector)
    created_at = models.DateTimeField(auto_now_add=True)


class RecommendationLog(models.Model):  # Renamed for clarity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="logId")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    style_image = models.ForeignKey(StyleImage, on_delete=models.CASCADE)
    recommended_products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)


class Feedback(models.Model):  # Renamed for clarity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="feedbackId")
    log = models.ForeignKey(RecommendationLog, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_good = models.BooleanField()
