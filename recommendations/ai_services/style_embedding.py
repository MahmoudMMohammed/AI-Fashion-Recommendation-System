# ai_services/style_embedding.py

import json
import subprocess
from celery import shared_task
from django.db import transaction
import os

# استيراد الموديلات
from ..models import ImageSegment, StyleEmbedding
from .recommender_service import get_recommendations


@shared_task
def process_style_embedding(image_segment_id, gender=None):
    """
    Celery task to generate style embedding for an ImageSegment.
    Uses singleton model for better performance - loads once, reuses many times.
    """
    try:
        segment = ImageSegment.objects.get(segmentId=image_segment_id)
    except ImageSegment.DoesNotExist:
        print(f"ImageSegment with id {image_segment_id} not found.")
        return

    # Path to the image segment
    image_path = segment.image_url.path

    # Use the singleton approach for better performance
    # The model will be loaded only once and reused for all subsequent calls
    try:
        # Path to the virtual environment's python interpreter
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        venv_python = os.path.join(project_root, 'style2vec_env', 'Scripts', 'python.exe')

        # Path to the singleton script
        script_path = os.path.join(current_dir, 'style2vec_singleton.py')

        # Run the singleton script in the style2vec_env
        result = subprocess.run(
            [venv_python, script_path, image_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the JSON output
        json_line = None
        for line in result.stdout.splitlines():
            if line.strip().startswith('{'):
                json_line = line
                break

        if json_line:
            embedding_data = json.loads(json_line)
            embedding_vector = embedding_data.get('embedding')
        else:
            print("Failed to find JSON output from the script.")
            return "Failed to find JSON output."

        if embedding_vector:
            with transaction.atomic():
                embedding = StyleEmbedding.objects.create(
                    segment=segment,
                    embeddings=embedding_vector
                )
                print(f"Embedding complete for segment {segment.segmentId}.")

            # Get recommendations (filtered by gender if provided)
            recommended_products = get_recommendations(image_segment_id, gender=gender)
            print(f"Recommendations found: {[p.name for p in recommended_products]}")
            return f"Embedding complete and recommendations found for segment {segment.segmentId}"
        else:
            print("Failed to get embedding vector from the script.")
            return "Failed to get embedding vector."

    except subprocess.CalledProcessError as e:
        print(f"Error running the embedding script: {e}")
        print(f"Stderr: {e.stderr}")
        return f"Error during embedding generation: {e}"
    except json.JSONDecodeError:
        print("Failed to decode JSON from script output.")
        return "JSON decode error."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"
