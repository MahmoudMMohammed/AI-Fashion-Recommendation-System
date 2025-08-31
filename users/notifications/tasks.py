# notifications/tasks.py
from celery import shared_task
from users.models import User
from .service import send_notification

@shared_task
def send_notification_task(user_id, title, message, payload=None, **kwargs):
    try:
        user = User.objects.get(id=user_id)
        send_notification(user, title, message, payload, **kwargs)
    except User.DoesNotExist:
        print(f"User with id {user_id} not found for notification task.")