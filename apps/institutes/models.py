from django.db import models

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name_bn = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, blank=True)
    code = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name_bn"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_bn


class Institute(TimeStampedModel):
    name_bn = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    institute_code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="institutes")
    address = models.CharField(max_length=255, blank=True)
    village = models.CharField(max_length=120, blank=True)
    post_office = models.CharField(max_length=120, blank=True)
    upazila = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name_bn"]
        indexes = [
            models.Index(fields=["name_bn"]),
            models.Index(fields=["district"]),
        ]

    def __str__(self):
        return self.name_bn
