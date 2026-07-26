import secrets

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Company


@receiver(pre_save, sender=User)
def mark_user_was_adding(sender, instance, **kwargs):
    # Capture state before save because post_save runs after _state.adding flips.
    instance._was_adding = instance._state.adding


@receiver(post_save, sender=User)
def create_company_profile(sender, instance, **kwargs):
    if getattr(instance, '_was_adding', False):
        Company.objects.get_or_create(
            user=instance,
            defaults={
                'company_name': instance.email or instance.username,
                'api_key': secrets.token_urlsafe(32),
            },
        )
