from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.models import TimeStampedModel


class AwardType(TimeStampedModel):
    name_bn = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name_bn"]

    def __str__(self):
        return self.name_bn


class ExamResult(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "খসড়া"
        APPROVED = "APPROVED", "অনুমোদিত"

    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="results")
    examination = models.ForeignKey("examinations.Examination", on_delete=models.PROTECT, related_name="results")
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    position = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entered_results",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_results",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "examination"], name="unique_result_per_student_exam"),
            models.CheckConstraint(
                condition=Q(obtained_marks__gte=0) & Q(obtained_marks__lte=F("total_marks")),
                name="obtained_marks_within_total",
            ),
        ]

    def __str__(self):
        return f"{self.student.student_id} · {self.examination}"

    def clean(self):
        if self.obtained_marks is not None and self.obtained_marks < 0:
            raise ValidationError({"obtained_marks": "নম্বর ঋণাত্মক হতে পারবে না।"})
        if (
            self.obtained_marks is not None
            and self.total_marks is not None
            and self.obtained_marks > self.total_marks
        ):
            raise ValidationError({"obtained_marks": "প্রাপ্ত নম্বর মোট নম্বরের বেশি হতে পারবে না।"})
        if self.student_id and self.examination_id:
            if self.student.scholarship_session_id != self.examination.scholarship_session_id:
                raise ValidationError("শিক্ষার্থী ও পরীক্ষা একই সেশনের হতে হবে।")
            if self.student.academic_class_id != self.examination.academic_class_id:
                raise ValidationError("শিক্ষার্থীর শ্রেণি পরীক্ষার শ্রেণির সাথে মিলছে না।")


class Winner(TimeStampedModel):
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="awards")
    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.PROTECT,
        related_name="winners",
    )
    award_type = models.ForeignKey(AwardType, on_delete=models.PROTECT, related_name="winners")
    position = models.PositiveIntegerField(null=True, blank=True)
    scholarship_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    result_reference = models.ForeignKey(
        ExamResult,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="winner_links",
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_winners",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "scholarship_session"],
                name="one_award_per_student_session",
            ),
            models.CheckConstraint(
                condition=Q(scholarship_amount__isnull=True) | Q(scholarship_amount__gte=0),
                name="winner_amount_non_negative",
            ),
        ]
        ordering = ["position", "award_type__display_order", "student__name_bn"]

    def __str__(self):
        return f"{self.student.student_id} · {self.award_type}"

    def clean(self):
        if self.student_id and self.scholarship_session_id:
            if self.student.scholarship_session_id != self.scholarship_session_id:
                raise ValidationError("শিক্ষার্থী এই স্কলারশিপ সেশনের নয়।")
        if self.scholarship_amount is not None and self.scholarship_amount < 0:
            raise ValidationError({"scholarship_amount": "টাকার পরিমাণ ঋণাত্মক হতে পারবে না।"})
        if self.result_reference_id and self.result_reference.student_id != self.student_id:
            raise ValidationError({"result_reference": "ফলাফল এই শিক্ষার্থীর নয়।"})
        if self.award_type_id and not self.award_type.is_active:
            raise ValidationError({"award_type": "নিষ্ক্রিয় পুরস্কার নির্বাচন করা যাবে না।"})
