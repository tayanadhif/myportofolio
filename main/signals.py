from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import UserProfile


@receiver(post_save, sender=get_user_model())
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"full_name": instance.get_full_name() or instance.username},
        )
