from PIL import Image
from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation, logging
import torch
import numpy as np

logging.set_verbosity_error()


class SegFormerSegmenter:
    """
    A singleton service to handle clothing segmentation using a SegFormer model.
    """
    _instance = None

    # This makes it a singleton - the model is only loaded into memory once.
    def __new__(cls):
        if cls._instance is None:
            print("Initializing SegFormer model for the first time...")
            cls._instance = super(SegFormerSegmenter, cls).__new__(cls)

            # --- Model Initialization ---
            cls._instance.model_name = "mattmdjaga/segformer_b2_clothes"
            cls._instance.processor = SegformerImageProcessor.from_pretrained(cls._instance.model_name)
            cls._instance.model = AutoModelForSemanticSegmentation.from_pretrained(cls._instance.model_name)
            cls._instance.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._instance.model.to(cls._instance.device).eval()
            print(f"SegFormer model loaded onto device: {cls._instance.device}")

            # --- Category Mapping and Exclusion Logic ---
            id2label = cls._instance.model.config.id2label
            cls._instance.categories_to_drop = {
                'Background', 'Hair', 'Face', 'Left-leg',
                'Right-leg', 'Left-arm', 'Right-arm', 'Left-shoe'
            }
            # This dictionary will hold the final mapping from the label name we care about
            # to its corresponding ID from the model.
            cls._instance.label_map = {}
            for lbl_id, lbl_name in id2label.items():
                if lbl_name in cls._instance.categories_to_drop:
                    continue  # Skip this category

                # Remap 'Right-shoe' to our database category 'Footwear'
                if lbl_name == 'Right-shoe':
                    final_category_name = 'Footwear'
                # Standardize category names to be lowercase for consistent DB lookups
                else:
                    final_category_name = lbl_name.lower().replace('-', ' ')

                cls._instance.label_map[final_category_name] = int(lbl_id)

        return cls._instance

    def run_segmentation(self, image_path):
        """
        Takes the path to an image and returns a dictionary of:
        { 'category_name': <PIL.Image object of the RGBA segment> }
        """
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return {}

        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        logits = outputs.logits

        # --- Upsample logits and get prediction mask ---
        upsampled = torch.nn.functional.interpolate(
            logits,
            size=image.size[::-1],  # (width, height) for Pillow
            mode="bilinear",
            align_corners=False
        )
        prediction_mask = upsampled.argmax(dim=1)[0].cpu().numpy()

        original_image_np = np.array(image)
        segmented_images = {}

        # Use our pre-filtered and remapped label map
        for category_name, label_id in self.label_map.items():
            # Create a boolean mask for the current category
            class_mask = (prediction_mask == label_id)

            # If any pixel belongs to this class, extract it
            if class_mask.any():
                # Create a blank RGBA image (all pixels transparent)
                rgba_segment = np.zeros((*original_image_np.shape[:2], 4), dtype=np.uint8)

                # Copy the original image's colors (RGB channels)
                rgba_segment[..., :3] = original_image_np

                # Set the Alpha channel: 255 (opaque) where the mask is true, 0 (transparent) otherwise
                rgba_segment[..., 3] = class_mask * 255

                # Convert the NumPy array back to a PIL Image object
                segment_pil = Image.fromarray(rgba_segment)

                segmented_images[category_name] = segment_pil

        return segmented_images
