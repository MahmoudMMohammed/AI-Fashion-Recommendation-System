import cv2
import numpy as np
import subprocess
import json
import os
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction

# استيراد الموديلات
from .models import StyleImage, ImageSegment, Category
from .ai_services.mmfashion_detector import MMFashionDetector
from .ai_services.fast_sam_segmenter import FastSAMSegmenter

# استيراد مهمة الـ Embedding الجديدة
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
        style_image = StyleImage.objects.get(styleImageId=style_image_id)
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

    return f"Segmentation complete for StyleImage {style_image_id}. Detected: {detected_categories}"

# import cv2
# import numpy as np
# from celery import shared_task
# from django.core.files.base import ContentFile
# from .models import StyleImage, ImageSegment, Category
# from .ai_services.mmfashion_detector import MMFashionDetector
# from .ai_services.fast_sam_segmenter import FastSAMSegmenter

# # Initialize models once when the worker starts, not for every task.
# detector = MMFashionDetector()
# segmenter = FastSAMSegmenter()


# @shared_task
# def process_style_image_segmentation(style_image_id):
#     """
#     Celery task to perform AI segmentation on a StyleImage.
#     """
#     try:
#         style_image = StyleImage.objects.get(styleImageId=style_image_id)
#     except StyleImage.DoesNotExist:
#         # Handle case where the image was deleted before processing
#         return f"StyleImage with id {style_image_id} not found."

#     image_path = style_image.image_url.path

#     # Stage 1: Detect all categories in the image
#     detected_categories = detector.detect_categories(image_path)
#     if not detected_categories:
#         return f"No categories detected for StyleImage {style_image_id}."

#     # Stage 2: For each category, segment the object and save it
#     for category_name in detected_categories:
#         # Segment the object
#         segment_image_np = segmenter.segment_object(image_path, category_name)

#         if segment_image_np is not None:
#             # Find the corresponding Category model instance
#             try:
#                 category_obj = Category.objects.get(name__iexact=category_name)
#             except Category.DoesNotExist:
#                 print(f"Category '{category_name}' not found in database. Skipping segment.")
#                 continue

#             # Convert numpy array to a Django file
#             _, buffer = cv2.imencode('.jpg', segment_image_np)
#             image_content = ContentFile(buffer.tobytes())

#             # Create the ImageSegment instance
#             segment = ImageSegment.objects.create(
#                 style_image=style_image,
#                 category_type=category_obj
#             )

#             # Save the image to the ImageField
#             # Django will automatically handle saving it to the correct path
#             segment_filename = f"{style_image_id}_{category_name}_segment.jpg"
#             segment.image_url.save(segment_filename, image_content, save=True)

#     return f"Segmentation complete for StyleImage {style_image_id}. Detected: {detected_categories}"