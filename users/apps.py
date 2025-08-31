import os
from django.apps import AppConfig
from django.conf import settings
import firebase_admin


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Initialize Firebase Admin SDK
        # The GOOGLE_APPLICATION_CREDENTIALS environment variable is used automatically
        # by the firebase_admin library if it's set.
        try:
            # We must check if the app is already initialized
            if not firebase_admin._apps:
                cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if cred_path:
                    creds = firebase_admin.credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(creds)
                    print("Firebase Admin SDK initialized successfully.")
                else:
                    print("GOOGLE_APPLICATION_CREDENTIALS path not found. Firebase not initialized.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
