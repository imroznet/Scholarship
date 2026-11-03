from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


class AcademicClass(TimeStampedModel):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=20, unique=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name_bn"]
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name_bn


class ClassRegistrationSetting(TimeStampedModel):
    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="class_registrations",
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        related_name="registration_settings",
    )
    is_open = models.BooleanField(default=False)
    opening_at = models.DateTimeField(null=True, blank=True)
    closing_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scholarship_session", "academic_class"],
                name="unique_class_registration_per_session",
            )
        ]
        ordering = ["academic_class__display_order", "academic_class__name_bn"]

    def __str__(self):
        return f"{self.scholarship_session.code} · {self.academic_class}"

    def is_currently_open(self, at=None):
        if not self.is_open or not self.academic_class.is_active:
            return False
        moment = at or timezone.now()
        if self.opening_at and moment < self.opening_at:
            return False
        if self.closing_at and moment > self.closing_at:
            return False
        return True


def open_registration_settings(session, at=None):
    moment = at or timezone.now()
    return (
        ClassRegistrationSetting.objects.filter(
            scholarship_session=session,
            is_open=True,
            academic_class__is_active=True,
        )
        .filter(Q(opening_at__isnull=True) | Q(opening_at__lte=moment))
        .filter(Q(closing_at__isnull=True) | Q(closing_at__gte=moment))
        .select_related("academic_class")
        .order_by("academic_class__display_order", "academic_class__name_bn")
    )
