import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.verification.statuses import VerificationStatus

MOBILE_PATTERN = r"^01[3-9]\d{8}$"


def student_photo_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    if ext not in {"png", "jpg", "jpeg", "webp"}:
        ext = "jpg"
    return f"private/students/{uuid.uuid4().hex}.{ext}"


class StudentQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)


class StudentSequence(TimeStampedModel):
    scholarship_session = models.OneToOneField(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="student_sequence",
    )
    prefix = models.CharField(max_length=20)
    last_number = models.PositiveIntegerField(default=0)
    certificate_last_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.prefix


class Student(TimeStampedModel):
    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.PROTECT,
        related_name="students",
    )
    student_id = models.CharField(max_length=32, unique=True)
    name_bn = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    photo = models.ImageField(upload_to=student_photo_path)
    date_of_birth = models.DateField()
    mobile = models.CharField(max_length=11)
    father_name = models.CharField(max_length=150, blank=True)
    father_mobile = models.CharField(max_length=11, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    mother_mobile = models.CharField(max_length=11, blank=True)
    village = models.CharField(max_length=120)
    post_office = models.CharField(max_length=120)
    upazila = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    institute = models.ForeignKey(
        "institutes.Institute",
        on_delete=models.PROTECT,
        related_name="students",
    )
    category = models.ForeignKey(
        "institutes.Category",
        on_delete=models.PROTECT,
        related_name="students",
    )
    category_name_bn = models.CharField(max_length=100)
    academic_class = models.ForeignKey(
        "academics.AcademicClass",
        on_delete=models.PROTECT,
        related_name="students",
    )
    verification_status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registered_students",
    )
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = StudentQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mobile"]),
            models.Index(fields=["name_bn"]),
            models.Index(fields=["scholarship_session", "deleted_at"]),
            models.Index(fields=["academic_class"]),
            models.Index(fields=["institute"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.student_id} · {self.name_bn}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def age_on(self, day):
        return day.year - self.date_of_birth.year - (
            (day.month, day.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def clean(self):
        import re

        from apps.core.models import WebsiteSetting

        errors = {}
        if self.mobile and not re.fullmatch(MOBILE_PATTERN, self.mobile):
            errors["mobile"] = "মোবাইল নম্বর 01XXXXXXXXX ফরম্যাটে দিন।"
        for field in ("father_mobile", "mother_mobile"):
            value = getattr(self, field)
            if value and not re.fullmatch(MOBILE_PATTERN, value):
                errors[field] = "মোবাইল নম্বর 01XXXXXXXXX ফরম্যাটে দিন।"
        settings_obj = WebsiteSetting.load()
        if settings_obj.parent_fields_required:
            for field in ("father_name", "father_mobile", "mother_name", "mother_mobile"):
                if not getattr(self, field):
                    errors[field] = "এই ঘরটি আবশ্যক।"
        if self.date_of_birth:
            today = timezone.localdate()
            if self.date_of_birth >= today:
                errors["date_of_birth"] = "জন্ম তারিখ অতীতের হতে হবে।"
            else:
                age = self.age_on(today)
                if age < settings_obj.min_student_age or age > settings_obj.max_student_age:
                    errors["date_of_birth"] = (
                        f"বয়স {settings_obj.min_student_age} থেকে {settings_obj.max_student_age} বছরের মধ্যে হতে হবে।"
                    )
        if self.institute_id and self.category_id and self.institute.category_id != self.category_id:
            errors["category"] = "বিভাগ প্রতিষ্ঠানের বিভাগের সাথে মিলতে হবে।"
        if errors:
            raise ValidationError(errors)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active", "updated_at"])
