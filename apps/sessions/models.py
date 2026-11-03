from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class ScholarshipSession(TimeStampedModel):
    name_bn = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    code = models.CharField(max_length=10, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date", "-code"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="unique_active_scholarship_session",
            )
        ]

    def __str__(self):
        return self.name_bn
