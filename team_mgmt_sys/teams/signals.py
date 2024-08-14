from django.db.models.signals import pre_save
from django.dispatch import receiver
from teams.models import Team
from django.utils.text import slugify


@receiver(pre_save, sender=Team)
def auto_generate_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)
