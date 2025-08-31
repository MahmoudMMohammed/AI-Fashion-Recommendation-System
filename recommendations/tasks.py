import cv2
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from users.notifications.tasks import send_notification_task

from .models import StyleImage, ImageSegment, Category
from .ai_services.mmfashion_detector import MMFashionDetector
from .ai_services.fast_sam_segmenter import FastSAMSegmenter

from .ai_services.style_embedding import process_style_embedding

# Initialize models once when the worker starts, not for every task.
detector = MMFashionDetector()
segmenter = FastSAMSegmenter()


@shared_task
def process_style_image_segmentation(style_image_id):
    """
    Celery task to perform AI segmentation on a StyleImage.
    """
    print(f"Processing segmentation for image ID: {style_image_id}")
    try:
        style_image = (
            StyleImage.objects
            .select_related("user")
            .get(styleImageId=style_image_id)
        )
        user_id = style_image.user_id
    except StyleImage.DoesNotExist:
        return f"StyleImage with id {style_image_id} not found."

    image_path = style_image.image_url.path

    # Stage 1: Detect all categories in the image
    detected_categories = detector.detect_categories(image_path)
    if not detected_categories:
        return f"No categories detected for StyleImage {style_image_id}."

    # Stage 2: For each category, segment the object and save it
    for category_name in detected_categories:
        segment_image_np = segmenter.segment_object(image_path, category_name)

        if segment_image_np is not None:
            try:
                category_obj = Category.objects.get(name__iexact=category_name)
            except Category.DoesNotExist:
                print(f"Category '{category_name}' not found in database. Skipping segment.")
                continue

            _, buffer = cv2.imencode('.jpg', segment_image_np)
            image_content = ContentFile(buffer.tobytes())

            # Use a transaction to ensure atomicity
            with transaction.atomic():
                segment = ImageSegment.objects.create(
                    style_image=style_image,
                    category_type=category_obj
                )
                segment_filename = f"{style_image_id}_{category_name}_segment.jpg"
                segment.image_url.save(segment_filename, image_content, save=True)

            # --- TRIGGER THE EMBEDDING TASK ---
            # Call the new task to process the created segment
            process_style_embedding.delay(segment.segmentId)
            print(f"Triggered embedding task for segment ID: {segment.segmentId}")

    send_notification_task.delay(
        user_id=user_id,
        title="Results are ready!",
        message=f"We found 10 products that fit your style.",
        payload={"style_image": style_image},
    )

    return f"Segmentation complete for StyleImage {style_image_id}. Detected: {detected_categories}"
