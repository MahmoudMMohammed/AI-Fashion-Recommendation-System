import os
from celery import Celery
import firebase_admin
from firebase_admin import credentials
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fashionRecommendationSystem.settings')

app = Celery('style_recommender')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


def initialize_firebase_for_celery():
    """Initializes the Firebase Admin SDK for Celery worker processes."""
    # This check prevents re-initializing the app, which would cause an error.
    if not firebase_admin._apps:
        print("Celery Worker: Initializing Firebase App...")
        try:
            relative_path = "users/notifications/firebase-admin-sdk.json"
            cred_path = os.path.join(settings.BASE_DIR, relative_path)
            print(f"Celery Worker: Attempting to load credentials from: {cred_path}")
            creds = credentials.Certificate(cred_path)

            firebase_admin.initialize_app(creds)
            print("Celery Worker: Firebase App Initialized.")
        except Exception as e:
            # Log any errors during initialization
            print(f"Celery Worker ERROR: Failed to initialize Firebase App: {e}")


# Run the initialization function when this module is loaded.
initialize_firebase_for_celery()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
