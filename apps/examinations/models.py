from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class Examination(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "খসড়া"
        PUBLISHED = "PUBLISHED", "প্রকাশিত"

    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="examinations",
    )
    academic_class = models.ForeignKey(
        "academics.AcademicClass",
        on_delete=models.PROTECT,
        related_name="examinations",
    )
    name_bn = models.CharField(max_length=255)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    total_marks = models.PositiveIntegerField(default=100)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["exam_date", "start_time"]

    def __str__(self):
        return self.name_bn

    def clean(self):
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "পরীক্ষা শেষ হওয়ার সময় শুরুর পরে হতে হবে।"})
        if self.total_marks <= 0:
            raise ValidationError({"total_marks": "মোট নম্বর শূন্যের বেশি হতে হবে।"})
