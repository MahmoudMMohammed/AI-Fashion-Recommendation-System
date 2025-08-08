import numpy as np
import cv2
import ailia

# NOTE: You will need to manage the models (WEIGHT_PATH, etc.)
# It's best to place them in a dedicated 'models' directory at the project root.
# For simplicity, we assume they are discoverable.
WEIGHT_PATH = './ai_models/mask_rcnn_r50_fpn_1x.onnx'
MODEL_PATH = './ai_models/mask_rcnn_r50_fpn_1x.onnx.prototxt'
REMOTE_PATH = 'https://storage.googleapis.com/ailia-models/mmfashion/'

CATEGORY_NAMES = (
    'top', 'skirt', 'leggings', 'dress', 'outer', 'pants', 'bag',
    'neckwear', 'headwear', 'eyeglass', 'belt', 'footwear', 'hair',
    'skin', 'face'
)


# ... (All your preprocess, post_processing, etc., functions go here)
# ... but we will refactor recognize_from_image to be a class method.

class MMFashionDetector:
    def __init__(self):
        # check_and_download_models(WEIGHT_PATH, MODEL_PATH, REMOTE_PATH)
        self.detector = ailia.Net(MODEL_PATH, WEIGHT_PATH)
        self.category_names = CATEGORY_NAMES

    def detect_categories(self, image_path):
        """
        Takes an image path and returns a list of detected category names.
        """
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # This function combines your old detect_objects and part of recognize_from_image
        data = self._preprocess(img)
        self.detector.set_input_shape((1, 3, data['img'].shape[2], data['img'].shape[3]))
        output = self.detector.predict({'image': data['img']})
        boxes, labels, masks = output

        # Simplified post-processing to just get category names
        detected_category_indices = set(labels[boxes[:, -1] > THRESHOLD])
        detected_categories = [self.category_names[i] for i in detected_category_indices]

        return detected_categories

    def _preprocess(self, img):
        # Your exact preprocess function from the script
        h, w = img.shape[:2]
        max_long_edge = max(RESIZE_RANGE)
        max_short_edge = min(RESIZE_RANGE)
        scale_factor = min(max_long_edge / max(h, w), max_short_edge / min(h, w))
        new_w = int(w * float(scale_factor) + 0.5)
        new_h = int(h * float(scale_factor) + 0.5)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        img = img.astype(np.float32)
        mean = np.array(NORM_MEAN)
        std = np.array(NORM_STD)
        mean = np.float64(mean.reshape(1, -1))
        stdinv = 1 / np.float64(std.reshape(1, -1))
        cv2.subtract(img, mean, img)
        cv2.multiply(img, stdinv, img)
        divisor = 32
        pad_h = int(np.ceil(img.shape[0] / divisor)) * divisor
        pad_w = int(np.ceil(img.shape[1] / divisor)) * divisor
        img = cv2.copyMakeBorder(img, 0, pad_h - img.shape[0], 0, pad_w - img.shape[1], cv2.BORDER_CONSTANT, value=0)
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, 0)
        return {'img': img}


# Constants from your script
THRESHOLD = 0.6
RESIZE_RANGE = (750, 1101)
NORM_MEAN = [123.675, 116.28, 103.53]
NORM_STD = [58.395, 57.12, 57.375]