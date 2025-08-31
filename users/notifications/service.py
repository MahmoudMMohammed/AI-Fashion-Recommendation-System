import firebase_admin
from firebase_admin import messaging
from users.models import Notification
from users.models import User


def send_notification(user: User, title: str, message: str, payload: dict = None, **kwargs):
    if payload is None:
        payload = {}

    try:
        notification_obj = Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            payload=payload,
        )
    except Exception as e:
        print(f"Error creating notification in DB: {e}")
        return None

    if not user.fcm_token:
        print(f"User {user.username} does not have an FCM token. Skipping push notification.")
        return notification_obj

    fcm_message = messaging.Message(
        notification=messaging.Notification(title=title, body=message),
        data={
            "notification_id": str(notification_obj.id),
            "title": title,
            "message": message,
            "type": notification_obj.type,
            "payload": str(payload),
        },
        token=user.fcm_token,
    )

    try:
        response = messaging.send(fcm_message)
        print(f"Successfully sent message: {response}")

    # CORRECT: The exception is on the `messaging` module
    except messaging.UnregisteredError:
        print(f"FCM token for user {user.username} is invalid/unregistered. Deleting it.")
        user.fcm_token = None
        user.save()

    except Exception as e:
        # Catch other potential errors
        print(f"Error sending FCM notification: {e}")

    return notification_obj