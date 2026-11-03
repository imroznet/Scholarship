from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WebsiteSetting(TimeStampedModel):
    """Singleton application settings edited by the super admin."""

    parent_fields_required = models.BooleanField(default=True)
    min_student_age = models.PositiveSmallIntegerField(default=5)
    max_student_age = models.PositiveSmallIntegerField(default=30)
    max_photo_mb = models.PositiveSmallIntegerField(
        default=2, validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    max_logo_mb = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    max_attachment_mb = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    students_per_page = models.PositiveSmallIntegerField(
        default=20, validators=[MinValueValidator(5), MaxValueValidator(100)]
    )

    class Meta:
        verbose_name = "Website setting"
        verbose_name_plural = "Website settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Application settings"
