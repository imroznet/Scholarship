import uuid

from django.utils.text import slugify

from apps.notices.models import Notice


def unique_slug(title, instance=None):
    base = slugify(title, allow_unicode=True)[:180] or f"notice-{uuid.uuid4().hex[:8]}"
    slug = base
    index = 2
    queryset = Notice.objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        slug = f"{base}-{index}"
        index += 1
    return slug
