import io

from celery import shared_task
from django.core.files.base import ContentFile
from users.notifications.tasks import send_notification_task

from .models import StyleImage, ImageSegment, Category
# from .ai_services.mmfashion_detector import MMFashionDetector
# from .ai_services.fast_sam_segmenter import FastSAMSegmenter

from .ai_services.style_embedding import process_style_embedding
from .ai_services.segformer_segmenter import SegFormerSegmenter

# Initialize models once when the worker starts, not for every task.
# detector = MMFashionDetector()
# segmenter = FastSAMSegmenter()
segmenter = SegFormerSegmenter()


@shared_task
def process_style_image_segmentation(style_image_id, gender=None):
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

    segmented_images = segmenter.run_segmentation(image_path)

    if not segmented_images:
        return f"No valid segments found for StyleImage {style_image_id}."

    saved_categories = []
    for category_name, segment_pil_image in segmented_images.items():
        try:
            # Look up the category in our database. The names from the service are already lowercase.
            category_obj = Category.objects.get(name__iexact=category_name)
        except Category.DoesNotExist:
            print(f"WARNING: Category '{category_name}' found by AI but does not exist in the database. Skipping.")
            continue

        # --- Save the PIL Image to the ImageField ---
        # Create a new ImageSegment instance
        segment = ImageSegment.objects.create(
            style_image=style_image,
            category_type=category_obj
        )

        # Convert PIL RGBA image to bytes in-memory
        buffer = io.BytesIO()
        segment_pil_image.save(buffer, format='PNG')  # Save as PNG to keep transparency
        image_content = ContentFile(buffer.getvalue())

        # Save the content to the ImageField
        segment_filename = f"{style_image_id}_{category_name}.png"
        segment.image_url.save(segment_filename, image_content, save=True)

        saved_categories.append(category_name)

        # --- TRIGGER THE EMBEDDING TASK ---
        # Call the new task to process the created segment
        process_style_embedding.delay(segment.segmentId, gender)
        print(f"Triggered embedding task for segment ID: {segment.segmentId}")

    send_notification_task.delay(
        user_id=user_id,
        title="Results are ready!",
        message=f"We found {len(saved_categories) * 10} products that fit your style.",
        payload={"style_image": str(style_image)},
    )

    return f"Segmentation complete for StyleImage {style_image_id}. Saved segments for: {saved_categories}"
