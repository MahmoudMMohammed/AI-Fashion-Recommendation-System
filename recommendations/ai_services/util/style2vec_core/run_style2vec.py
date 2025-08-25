from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import sys
import os
import time
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # استخدم أول GPU
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import datetime
import json
import tensorflow as tf
import os
from tensorboard.plugins.hparams import api as hp
# from style2vec.data.sample_generator import SamplesGenerator

from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.layers import GlobalAveragePooling2D, Input

# To prevent tensorflow from occupying all the GPU_RAM
from keras import backend as K
config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.compat.v1.Session(config=config)
K.set_session(sess)

date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
dir_path = os.path.dirname(os.path.realpath(__file__))

##os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # استخدم أول GPU
base_logs_path = os.path.join(os.getcwd(), "logs")  # استخدم الدليل الحالي بشكل آمن
log_dir = os.path.join(base_logs_path, date)
os.makedirs(log_dir, exist_ok=True)

# تأكد من وجود المجلدات
os.makedirs(log_dir, exist_ok=True)
os.makedirs(os.path.join(log_dir, "chckpts"), exist_ok=True)

class Style2Vec:
    def build_base_model(self, name_prefix):
        base_model = InceptionV3(include_top=False, weights=None, input_shape=(299, 299, 3))
        
        # Try to load weights from local path first
        current_dir = os.path.dirname(os.path.abspath(__file__))
        inception_weights_path = os.path.abspath(os.path.join(
            current_dir, 
            '..', #util
            '..', #ai services
            '..', #recommendations
            '..', #AI_Fashion_Recommendations
            'ai_models', 
            'inception_v3_weights_tf_dim_ordering_tf_kernels_notop.h5'
        ))
        
        # Check if local weights exist, otherwise download from internet
        if os.path.exists(inception_weights_path):
            print(f"Loading Inception weights from local path: {inception_weights_path}")
            base_model.load_weights(inception_weights_path)
        else:
            print("Local Inception weights not found. Downloading from internet...")
            # Use Keras to download pre-trained weights
            base_model = InceptionV3(include_top=False, weights='imagenet', input_shape=(299, 299, 3))
            print("Inception weights downloaded successfully!")
            
            # Save the downloaded weights to local path for future use
            try:
                # Ensure the ai_models directory exists
                ai_models_dir = os.path.dirname(inception_weights_path)
                os.makedirs(ai_models_dir, exist_ok=True)
                
                # Save the weights
                base_model.save_weights(inception_weights_path)
                print(f"Inception weights saved to local path: {inception_weights_path}")
            except Exception as e:
                print(f"Warning: Could not save Inception weights locally: {e}")
                print("Weights will be downloaded again next time.")

        for i, layer in enumerate(base_model.layers):
            layer._name = f"{name_prefix}_{layer.name}"

        inputs = Input(shape=(299, 299, 3))
        x = base_model(inputs)
        x = GlobalAveragePooling2D(name=f'{name_prefix}_gap')(x)
        return tf.keras.Model(inputs=inputs, outputs=x)
    
    def __init__(self,
                 dataset_path: str,
                 images_path: str,
                 batch_size: int = 10,
                 epochs_count: int = 1,
                 outfits_count_limit: int = -1,
                 samples_count_limit: int = -1,
                 hparams=None):

        self.hparams = hparams
        self.epochs_count = epochs_count
        self.history = None
        # Create input layers
        input_target = tf.keras.layers.Input((299, 299, 3))
        input_context = tf.keras.layers.Input((299, 299, 3))

        self.model_target = self.build_base_model("target")
        self.model_context = self.build_base_model("context")

        # Rename layers
        for i, layer in enumerate(self.model_target.layers):
            layer._name = 'target_' + str(i)
            if i == len(self.model_target.layers) - 1:
                layer._name = 'target_last_layer'
        for i, layer in enumerate(self.model_context.layers):
            layer._name = 'context_' + str(i)
            if i == len(self.model_context.layers) - 1:
                layer._name = 'context_last_layer'

        if self.hparams and self.hparams.get(HP_FINE_TUNE) == True:
            # Set up fine-tuning
            base_target_model = self.model_target.layers[1]
            base_context_model = self.model_context.layers[1]

            # Freeze all but top layers
            for layer in base_target_model.layers[:249]:
                layer.trainable = False
            for layer in base_context_model.layers[:249]:
                layer.trainable = False

            for i, layer in enumerate(base_context_model.layers[249:]):
                print(i)
                layer.trainable = True
            for layer in base_target_model.layers[249:]:
                layer.trainable = True

        target_embedding = self.model_target(input_target)
        context_embedding = self.model_context(input_context)

        dot_product = tf.keras.layers.dot([target_embedding, context_embedding], axes=1)
        dot_product = tf.keras.layers.Reshape((1,))(dot_product)
        # output = tf.keras.layers.Dense(1, activation='sigmoid')(dot_product)

        # Sigmoid layer
        output = tf.keras.layers.Dense(1, activation='sigmoid')(dot_product)

        # Create model and generator

        self.model = tf.keras.Model(inputs=[input_target, input_context], outputs=output)
        # self.model = tf.keras.utils.multi_gpu_model(self.model, gpus=2)
        # استخدم النموذج كما هو دون التوزيع على عدة GPUs
        # (لأن النموذج قد تم بناؤه سابقًا في self.model = self.build_model(...) )
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    #     self.generator = SamplesGenerator(
    #         dataset_path,
    #         images_path,
    #         batch_size=batch_size,
    #         samples_count_limit=samples_count_limit,
    #         outfits_count_limit=outfits_count_limit
    #     )
    #     print("Style2Vec model has been successfully initialized.")

    # def fit(self):
    #     print("Model fitting has started.")
    #     self.generator.generate_samples()
    #     self.history = self.model.fit(
    #     self.generator.generate_batches(),
    #     steps_per_epoch=self.generator.steps_per_epoch,
    #     epochs=self.epochs_count,
    #     verbose=1,
    #     callbacks=[
    #             tf.keras.callbacks.TensorBoard(log_dir=log_dir, update_freq='epoch', write_graph=False),
    #             tf.keras.callbacks.ModelCheckpoint(filepath=os.path.join(log_dir, 'chckpts', 'weights.{epoch:02d}.weights.h5'),save_weights_only=True)
    #         ]
    #     )

    def plot_model(self):
        tf.keras.utils.plot_model(
            self.model,
            to_file=log_dir+'model.png',
            show_shapes=False,
            show_layer_names=True,
            rankdir='TB'
        )

    def save_weights(self, filepath: str):
        self.model.save_weights(filepath)

    def save_style2vec(self, model_filepath: str = 'model.h5'):
         self.model.save(model_filepath)
        ##self.model.save(os.path.join(log_dir, 'model_' + date + '.h5'))


HP_OPTIMIZER = hp.HParam('optimizer', hp.Discrete(['adam', 'sgd']))
HP_BATCH_SIZE = hp.HParam('batch_size', hp.Discrete([8, 16, 24, 32, 48]))
HP_NEGATIVE_SAMPLES = hp.HParam('negative_samples', hp.Discrete([6, 12, 18]))
HP_FINE_TUNE = hp.HParam('fine_tune', hp.Discrete([True, False]))

METRIC_ACCURACY = 'accuracy'

hyperparams = {
    HP_BATCH_SIZE: 5,
    HP_NEGATIVE_SAMPLES: 6,
    HP_OPTIMIZER: 'adam',
    HP_FINE_TUNE: True
}

if __name__ == '__main__':

    current_dir = os.path.dirname(os.path.abspath(__file__))
    model = Style2Vec(
        dataset_path=  os.path.abspath(os.path.join(current_dir, '..', '..', 'data', 'fixed_output_all_part.json')),
        # images_path="D:/Style2Vec-master/data/raw/images/",
        images_path= os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..', 'images')),
        batch_size=20, ##was 4         # <-- هنا حجم الباتش
        epochs_count=30,         # <-- عدد الإبوك واحد
        outfits_count_limit=-1, # (مثلاً خليها 50 أو -1 حسب رغبتك)
        samples_count_limit=-1, # <-- عدد العينات 100 فقط
        hparams=hyperparams     # تمرير هايبربارامترات لو حابب
    )

    try:
        start = time.time()
        print("Starting fit...")
        model.fit()
        print("Fit finished.")
        end = time.time()

        #print(model.model.inputs)  # should not be empty
        #print(model.model.outputs)  # should not be empty

        #json_path = os.path.join(current_dir, '..', '..', 'data', 'fixed_output.json')
        #model.save_style2vec(log_dir + '/model_' + date + '.h5')
        with open(log_dir + '/meta.txt', "w+") as time_file:
            time_file.write('batch 24, limit -1, adam, e 5, fine tune, neg 6\n')
            time_file.write(str(end - start))
        with open(log_dir + '/history.json', 'w') as f:
            json.dump(model.history.history, f)
        with open(log_dir + '/history_loss.txt', 'w') as f:
            json.dump(model.history.history["loss"], f)
        with open(log_dir + '/history_accuracy.txt', 'w') as f:
            json.dump(model.history.history["accuracy"], f)
        print("Successfully finished.")

        model.plot_model()
    except Exception as e:
        model.save(log_dir+ 'model_err.h5')
        with open(log_dir  + 'err.txt', "w+") as err_file:
            err_file.write(str(e))
        print(f"Exception occurred: {e}")

