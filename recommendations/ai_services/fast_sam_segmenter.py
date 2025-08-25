from ultralytics import FastSAM
import cv2
import numpy as np

# Map simple categories to more descriptive prompts
PROMPT_MAP = {
    'top': 'shirt, t-shirt or top',
    'outer': 'jacket, coat, or outer garment',
    'belt': 'a strip of leather or other material worn around the waist',
    'dress': 'long dress or skirt',
    'skirt': 'a garment hanging from the waist, like a skirt',
    'leggings': 'tight-fitting stretch pants, e.g. leggings',
    'bag': 'bag',
    'neckwear': 'accessory worn around the neck like a scarf, tie or necklace',
    'headwear': 'hat above the head',
    'eyeglass': 'glasses or sunglasses',
    'hair': 'hair on the head',
    'skin': 'exposed skin regions',
    'face': 'the face region including eyes, nose and mouth',
    'footwear': 'something worn in feets like shoes',
    'pants': 'pants, shorts or trousers',
    'default': ''
}


class FastSAMSegmenter:
    def __init__(self):
        # It's better to initialize the model once.
        self.model = FastSAM("./ai_models/FastSAM-x.pt")

    def segment_object(self, image_path, category_name):
        """
        Final robust version with added print statements for debugging shape mismatches.
        """
        source = cv2.imread(image_path)
        if source is None:
            print(f"[DEBUG] Error: Could not read image from path: {image_path}")
            return None

        prompt = PROMPT_MAP.get(category_name, category_name)

        # --- Run Inference ---
        print(f"[DEBUG] Running FastSAM for prompt: '{prompt}' on image with shape: {source.shape}")
        results = self.model(source, texts=prompt)

        if results[0].masks is None or len(results[0].masks.data) == 0:
            print(f"[DEBUG] FastSAM found no masks for prompt '{prompt}'")
            return None

        # --- Process Mask ---
        mask = results[0].masks.data[0].cpu().numpy()
        print(f"[DEBUG] Initial mask shape from model: {mask.shape}")

        # Let's get the height and width the model *actually* used for its output mask
        mask_h, mask_w = mask.shape[:2]

        # --- Prepare source image ---
        # The source image must be resized to match the mask dimensions for the cutout
        # Let's use the dimensions of the returned mask as the source of truth.
        source_rgb = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)

        if source_rgb.shape[:2] != (mask_h, mask_w):
            print(f"[DEBUG] Resizing source image from {source_rgb.shape[:2]} to match mask {(mask_h, mask_w)}")
            source_rgb = cv2.resize(source_rgb, (mask_w, mask_h))

        white_bg = np.ones_like(source_rgb) * 255

        # --- Final Shape Check Before Crashing Line ---
        mask_3d = mask.astype(np.uint8)[..., np.newaxis]

        print("-------------------- FINAL SHAPE CHECK --------------------")
        print(f"[DEBUG] Shape of mask_3d (condition):      {mask_3d.shape}")
        print(f"[DEBUG] Shape of source_rgb (choice 1):    {source_rgb.shape}")
        print(f"[DEBUG] Shape of white_bg (choice 2):      {white_bg.shape}")
        print("---------------------------------------------------------")

        # This is the line that fails
        cutout = np.where(mask_3d > 0, source_rgb, white_bg)

        # --- Crop to Bounding Box ---
        ys, xs = np.where(mask > 0)

        if len(xs) > 0 and len(ys) > 0:
            x_min, x_max = xs.min(), xs.max()
            y_min, y_max = ys.min(), ys.max()

            cropped_cutout = cutout[y_min:y_max + 1, x_min:x_max + 1]
            return cv2.cvtColor(cropped_cutout, cv2.COLOR_RGB2BGR)

        return None
