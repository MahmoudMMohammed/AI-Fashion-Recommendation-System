import io
import sys
import json
import os
import numpy as np
import tensorflow as tf
from PIL import ImageFile
from tensorflow.keras.utils import load_img
import requests
import gdown

# to prevent tensorflow from occupying all the GPU_RAM
from keras import backend as K

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.compat.v1.Session(config=config)
K.set_session(sess)

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Ensure the path to the Style2Vec model is correct
# adjust this path as needed to your project structure
style2vec_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'style2vec_core'))
sys.path.append(style2vec_core_path)
from run_style2vec import Style2Vec, HP_BATCH_SIZE, HP_NEGATIVE_SAMPLES, HP_OPTIMIZER, HP_FINE_TUNE

# Path to your Style2Vec model weights
MODEL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai_models', 'weights.19.weights.h5')

# Google Drive folder URL containing Style2Vec weights
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8"

# Available weights files in the Google Drive folder
AVAILABLE_WEIGHTS = {
    'weights.10.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8',
    'weights.19.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8',
    'weights.27.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8',
}

def download_weights_from_drive(weights_filename, target_path):
    """Download Style2Vec weights from Google Drive if not found locally."""
    try:
        # Ensure ai_models directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        print(f"Downloading {weights_filename} from Google Drive...")
        
        # Use gdown to download from Google Drive folder
        # We'll use the folder URL and specify the filename
        folder_id = AVAILABLE_WEIGHTS.get(weights_filename)
        if not folder_id:
            raise ValueError(f"Weights file {weights_filename} not found in available weights list")
        
        # Download using gdown with folder ID and filename
        gdown.download_folder(
            url=f"https://drive.google.com/drive/folders/{folder_id}",
            output=os.path.dirname(target_path),
            use_cookies=False
        )
        
        # Check if file was downloaded successfully
        if os.path.exists(target_path):
            print(f"Successfully downloaded {weights_filename} to {target_path}")
            return True
        else:
            print(f"Failed to download {weights_filename}")
            return False
            
    except Exception as e:
        print(f"Error downloading weights: {e}")
        return False

def ensure_weights_exist(weights_path, weights_filename):
    """Ensure Style2Vec weights exist, download from Google Drive if needed."""
    if os.path.exists(weights_path):
        print(f"Style2Vec weights found at: {weights_path}")
        return weights_path
    
    print(f"Style2Vec weights not found at: {weights_path}")
    print("Attempting to download from Google Drive...")
    
    if download_weights_from_drive(weights_filename, weights_path):
        return weights_path
    else:
        raise FileNotFoundError(
            f"Could not find or download Style2Vec weights. "
            f"Please manually download {weights_filename} from: {GOOGLE_DRIVE_FOLDER_URL}"
        )

def load_trained_model(model_path):
    """Load the trained Style2Vec model and its weights."""
    # Ensure weights exist before loading
    weights_filename = os.path.basename(model_path)
    model_path = ensure_weights_exist(model_path, weights_filename)
    
    # print("loading style2vec")
    # print("style2vec hparams initialized")
    hparams = {
        HP_BATCH_SIZE: 5,
        HP_NEGATIVE_SAMPLES: 6,
        HP_OPTIMIZER: 'adam',
        HP_FINE_TUNE: True
    }
    # print("style2vec hparams initialized")
    model = Style2Vec(
        dataset_path="", # This is a dummy path, as we don't need to train here
        images_path="",
        hparams=hparams,
        epochs_count=1
    )
    # The models need to be built before loading weights, which the __init__ does.
    # print("style2vec weights")
    model.model.load_weights(model_path)
    # print("style2vec weights loaded successfully")
    return model

def get_embedding(model, image_path, target='target'):
    """Extract embedding from an image."""
    try:
        img = load_img(image_path, target_size=(299, 299))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        # print("image preprocessed successfully")
        if target == 'target':
            embedding = model.model_target.predict(img_array)
        else:
            embedding = model.model_context.predict(img_array)
        
        # print("embedding ready on the way")
        return embedding.flatten().tolist()
    except Exception as e:
        print(f"Error processing image {image_path}: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_embedding.py <image_path>", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Load the model only once
    # print("Loading!!")
    style_model = load_trained_model(MODEL_WEIGHTS_PATH)
    
    # Get the embedding
    # print("Embedding!!")
    embedding_vector = get_embedding(style_model, image_path)
    
    # Print the embedding as a JSON string to be captured by the parent process
    if embedding_vector:
        print(json.dumps({'embedding': embedding_vector}))
    else:
        sys.exit(1)