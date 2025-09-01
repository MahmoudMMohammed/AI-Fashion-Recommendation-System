"""
Style2Vec Singleton Model Loader
Loads the Style2Vec model once and reuses it for all embedding operations
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from PIL import ImageFile
from tensorflow.keras.utils import load_img
import gdown

# Configure TensorFlow to use GPU memory growth (modern approach)
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(f"GPU memory growth setting failed: {e}")

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Google Drive folder URL containing Style2Vec weights
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8"

# Available weights files in the Google Drive folder
AVAILABLE_WEIGHTS = {
    'weights.10.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8',
    'weights.19.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8',
    'weights.27.weights.h5': '1o1HGE9zSeLqrnWDcD-JA7acACnXiQYo8'
}

# Add Style2Vec core to path
style2vec_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'util', 'style2vec_core'))
sys.path.append(style2vec_core_path)

try:
    from run_style2vec import Style2Vec, HP_BATCH_SIZE, HP_NEGATIVE_SAMPLES, HP_OPTIMIZER, HP_FINE_TUNE
except ImportError as e:
    print(f"Error importing Style2Vec: {e}")
    print("Make sure you're running this in the style2vec_env virtual environment")
    raise

def download_weights_from_drive(weights_filename, target_path):
    """Download Style2Vec weights from Google Drive if not found locally."""
    try:
        # Ensure ai_models directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        print(f"Downloading {weights_filename} from Google Drive...")
        
        # Use gdown to download from Google Drive folder
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

class Style2VecSingleton:
    """
    Singleton class to load Style2Vec model once and reuse it
    """
    _instance = None
    _model = None
    _is_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Style2VecSingleton, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._is_loaded:
            self._load_model()
    
    def _load_model(self):
        """Load the Style2Vec model and weights"""
        try:
            print("Loading Style2Vec model (this happens only once)...")
            
            # Model weights path
            model_weights_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'ai_models', 
                'weights.27.weights.h5'
            )
            
            # Ensure weights exist, download from Google Drive if needed
            weights_filename = os.path.basename(model_weights_path)
            model_weights_path = ensure_weights_exist(model_weights_path, weights_filename)
            
            # Initialize model parameters
            hparams = {
                HP_BATCH_SIZE: 5,
                HP_NEGATIVE_SAMPLES: 6,
                HP_OPTIMIZER: 'adam',
                HP_FINE_TUNE: True
            }
            
            # Create and load the model
            self._model = Style2Vec(
                dataset_path="",  # Dummy path, not needed for inference
                images_path="",
                hparams=hparams,
                epochs_count=1
            )
            
            # Load the trained weights
            self._model.model.load_weights(model_weights_path)
            
            self._is_loaded = True
            print("Style2Vec model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading Style2Vec model: {e}")
            raise
    
    def get_embedding(self, image_path, target='target'):
        """
        Generate embedding for an image
        
        Args:
            image_path: Path to the image file
            target: 'target' or 'context' model to use
            
        Returns:
            list: Embedding vector as a list of floats
        """
        if not self._is_loaded:
            raise RuntimeError("Style2Vec model not loaded")
        
        try:
            # Load and preprocess image
            img = load_img(image_path, target_size=(299, 299))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array /= 255.0
            
            # Generate embedding
            if target == 'target':
                embedding = self._model.model_target.predict(img_array, verbose=0)
            else:
                embedding = self._model.model_context.predict(img_array, verbose=0)
            
            return embedding.flatten().tolist()
            
        except Exception as e:
            print(f"Error generating embedding for {image_path}: {e}")
            return None
    
    def is_loaded(self):
        """Check if model is loaded"""
        return self._is_loaded

# Global instance
style2vec_model = Style2VecSingleton()

def get_style2vec_embedding(image_path, target='target'):
    """
    Convenience function to get embedding from the singleton model
    
    Args:
        image_path: Path to the image file
        target: 'target' or 'context' model to use
        
    Returns:
        list: Embedding vector as a list of floats
    """
    return style2vec_model.get_embedding(image_path, target)

# For backward compatibility with subprocess approach
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python style2vec_singleton.py <image_path> [target|context]", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else 'target'
    
    try:
        embedding_vector = get_style2vec_embedding(image_path, target)
        
        if embedding_vector:
            # Output as JSON for subprocess compatibility
            print(json.dumps({'embedding': embedding_vector}))
        else:
            print("Failed to generate embedding", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 