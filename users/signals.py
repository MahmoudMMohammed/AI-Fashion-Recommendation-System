from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def activate_user(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        instance.is_active = True
        instance.save()
