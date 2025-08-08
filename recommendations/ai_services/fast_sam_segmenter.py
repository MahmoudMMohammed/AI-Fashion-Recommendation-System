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
    'bag': 'a flexible container for carrying items, such as a bag',
    'neckwear': 'accessory worn around the neck like a scarf, tie or necklace',
    'headwear': 'accessory worn on the head such as a hat, cap or headband',
    'eyeglass': 'corrective or protective eyewear, e.g. glasses',
    'hair': 'hair on the head',
    'skin': 'exposed skin regions',
    'face': 'the face region including eyes, nose and mouth',
    'footwear': 'shoes, boots or any covering worn on the feet',
    'pants': 'pants, shorts or trousers',
    'default': ''
}


class FastSAMSegmenter:
    def __init__(self):
        # It's better to initialize the model once.
        self.model = FastSAM("./ai_models/FastSAM-x.pt")

    def segment_object(self, image_path, category_name):
        """
        Takes an image path and a category name, returns the cropped segment image as a NumPy array.
        """
        source = cv2.imread(image_path)
        source_rgb = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
        h, w = source_rgb.shape[:2]

        prompt = PROMPT_MAP.get(category_name, category_name)

        results = self.model(source, texts=prompt)

        # Check if any masks were returned
        if results[0].masks is None or len(results[0].masks) == 0:
            return None  # No object found for this prompt

        masks = results[0].masks.data.cpu().numpy()
        mask = masks[0]
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

        # Create a white background and apply the mask
        white_bg = np.ones_like(source_rgb) * 255
        cutout = np.where(mask[..., None] > 0, source_rgb, white_bg)

        # Find the bounding box of the non-white object to crop it
        gray = cv2.cvtColor(cutout, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        ys, xs = np.where(binary > 0)

        if len(xs) > 0 and len(ys) > 0:
            x_min, x_max = xs.min(), xs.max()
            y_min, y_max = ys.min(), ys.max()
            cropped_cutout = cutout[y_min:y_max + 1, x_min:x_max + 1]
            # Convert back to BGR for saving with OpenCV/Django
            return cv2.cvtColor(cropped_cutout, cv2.COLOR_RGB2BGR)

        return None  # Return None if no object pixels were found