from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Schedule(TimeStampedModel):
    class Stage(models.TextChoices):
        APPLICATION = "APPLICATION", "আবেদন গ্রহণ"
        VERIFICATION = "VERIFICATION", "আবেদন যাচাই"
        EXAMINATION = "EXAMINATION", "পরীক্ষা"
        PROCESSING = "PROCESSING", "ফলাফল প্রস্তুতকরণ"
        PUBLICATION = "PUBLICATION", "ফলাফল প্রকাশ"

    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    stage = models.CharField(max_length=32, choices=Stage.choices)
    title_bn = models.CharField(max_length=255)
    description_bn = models.TextField(blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    countdown_target = models.DateTimeField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    show_countdown = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["scholarship_session", "stage"],
                name="unique_stage_per_session",
            ),
            models.UniqueConstraint(
                fields=["scholarship_session"],
                condition=Q(is_active=True),
                name="one_active_schedule_per_session",
            ),
        ]

    def __str__(self):
        return self.title_bn

    def clean(self):
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "শেষ সময় শুরুর সময়ের পরে হতে হবে।"})
        if self.is_active and (not self.start_at or not self.end_at):
            raise ValidationError("তারিখ ছাড়া পর্যায় সক্রিয় করা যাবে না।")
