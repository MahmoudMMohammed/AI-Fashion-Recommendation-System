from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import subprocess
import os
import json
from .models import Product, ProductImage


@receiver(post_save, sender=Product)
def generate_product_embedding(sender, instance, created, **kwargs):
    """
    Generate embedding for a product when it's created or updated.
    Uses the first product image to generate the embedding.
    """
    if created and instance.embedding is None:
        # Get the first product image
        first_image = instance.images.first()
        if first_image and first_image.image:
            try:
                # Generate embedding using Style2Vec
                embedding = generate_embedding_from_image(first_image.image.path)
                if embedding:
                    # Update the product with the generated embedding
                    instance.embedding = embedding
                    instance.save(update_fields=['embedding'])
                    print(f"Generated embedding for product: {instance.name}")
            except Exception as e:
                print(f"Error generating embedding for product {instance.name}: {e}")


def generate_embedding_from_image(image_path):
    """
    Generate embedding from an image using Style2Vec model.
    Uses the same approach as the existing generate_embedding.py script.
    """
    try:
        # Path to the virtual environment's python interpreter
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        venv_python = os.path.join(project_root, 'style2vec_env', 'Scripts', 'python.exe')
        
        # Path to the generate_embedding.py script
        script_path = os.path.join(project_root, 'recommendations', 'ai_services', 'util', 'generate_embedding.py')
        
        # Run the script using subprocess within the correct virtual environment
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
            return embedding_data.get('embedding')
        else:
            print("Failed to find JSON output from the script.")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running the embedding script: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON from script output.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


@receiver(post_save, sender=ProductImage)
def update_product_embedding_on_image_change(sender, instance, created, **kwargs):
    """
    Update product embedding when a new image is added and the product doesn't have an embedding.
    """
    if created and instance.product.embedding is None:
        try:
            # Generate embedding using the new image
            embedding = generate_embedding_from_image(instance.image.path)
            if embedding:
                # Update the product with the generated embedding
                instance.product.embedding = embedding
                instance.product.save(update_fields=['embedding'])
                print(f"Generated embedding for product: {instance.product.name} using new image")
        except Exception as e:
            print(f"Error generating embedding for product {instance.product.name}: {e}") 