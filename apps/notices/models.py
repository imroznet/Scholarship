import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


def notice_attachment_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    if ext not in {"pdf", "png", "jpg", "jpeg", "webp"}:
        ext = "bin"
    return f"private/notices/{uuid.uuid4().hex}.{ext}"


class Notice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "খসড়া"
        PUBLISHED = "PUBLISHED", "প্রকাশিত"
        ARCHIVED = "ARCHIVED", "আর্কাইভ"

    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="notices",
    )
    title_bn = models.CharField(max_length=255)
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True)
    content_bn = models.TextField()
    attachment = models.FileField(upload_to=notice_attachment_path, blank=True)
    attachment_name = models.CharField(max_length=120, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notices",
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self):
        return self.title_bn

    @property
    def is_publicly_visible(self):
        if self.status != self.Status.PUBLISHED:
            return False
        now = timezone.now()
        if self.published_at and self.published_at > now:
            return False
        if self.expires_at and self.expires_at <= now:
            return False
        return True


def public_notices(session, now=None):
    moment = now or timezone.now()
    return Notice.objects.filter(
        scholarship_session=session,
        status=Notice.Status.PUBLISHED,
    ).filter(Q(published_at__isnull=True) | Q(published_at__lte=moment)).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=moment)
    )
