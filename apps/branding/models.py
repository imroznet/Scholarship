import uuid

from django.core.exceptions import ValidationError
from django.db import models
from urllib.parse import urlparse

from apps.core.models import TimeStampedModel


def _extension(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    if ext not in {"png", "jpg", "jpeg", "webp"}:
        ext = "png"
    return ext


def _path(instance, filename, kind):
    session_id = instance.session_id or "new"
    return f"branding/session-{session_id}/{kind}/{uuid.uuid4().hex}.{_extension(filename)}"


def logo_path(instance, filename):
    return _path(instance, filename, "logo")


def logo_original_path(instance, filename):
    return _path(instance, filename, "logo-original")


def sponsor_logo_path(instance, filename):
    return _path(instance, filename, "sponsor-logo")


def sponsor_logo_original_path(instance, filename):
    return _path(instance, filename, "sponsor-logo-original")


def favicon_path(instance, filename):
    return _path(instance, filename, "favicon")


def secondary_logo_path(instance, filename):
    return _path(instance, filename, "secondary-logo")


def secondary_logo_original_path(instance, filename):
    return _path(instance, filename, "secondary-original")


def signature_path(instance, filename):
    return _path(instance, filename, "signature")


def seal_path(instance, filename):
    return _path(instance, filename, "seal")


class ScholarshipBranding(TimeStampedModel):
    session = models.OneToOneField(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.CASCADE,
        related_name="branding",
    )
    name_bn = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=10, default="CGS")
    slogan_bn = models.CharField(max_length=255, blank=True)
    description_bn = models.TextField(blank=True)
    about_bn = models.TextField(blank=True)
    objectives_bn = models.TextField(blank=True)
    eligibility_bn = models.TextField(blank=True)
    application_process_bn = models.TextField(blank=True)
    contact_info = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    sponsor_name_bn = models.CharField(max_length=255, blank=True)
    sponsor_name_en = models.CharField(max_length=255, blank=True)
    sponsor_description = models.TextField(blank=True)
    sponsor_website = models.URLField(blank=True)
    sponsor_contact = models.TextField(blank=True)

    logo = models.ImageField(upload_to=logo_path, blank=True)
    logo_original = models.FileField(upload_to=logo_original_path, blank=True)
    sponsor_logo = models.ImageField(upload_to=sponsor_logo_path, blank=True)
    sponsor_logo_original = models.FileField(upload_to=sponsor_logo_original_path, blank=True)
    favicon = models.ImageField(upload_to=favicon_path, blank=True)
    secondary_logo = models.ImageField(upload_to=secondary_logo_path, blank=True)
    secondary_logo_original = models.FileField(upload_to=secondary_logo_original_path, blank=True)

    certificate_title_bn = models.CharField(max_length=255, blank=True)
    certificate_footer_bn = models.TextField(blank=True)
    signatory_name_bn = models.CharField(max_length=255, blank=True)
    signatory_title_bn = models.CharField(max_length=255, blank=True)
    signature_image = models.ImageField(upload_to=signature_path, blank=True)
    seal_image = models.ImageField(upload_to=seal_path, blank=True)

    class Meta:
        verbose_name = "Scholarship branding"

    def __str__(self):
        return self.name_bn

    def clean(self):
        if self.sponsor_website:
            parsed = urlparse(self.sponsor_website)
            if parsed.scheme not in {"http", "https"}:
                raise ValidationError({"sponsor_website": "ওয়েবসাইট ঠিকানা http বা https হতে হবে।"})
        if self.short_name and not self.short_name.isalpha():
            raise ValidationError({"short_name": "সংক্ষিপ্ত নাম শুধু ইংরেজি অক্ষর হবে।"})

    def save(self, *args, **kwargs):
        if self.short_name:
            self.short_name = self.short_name.upper()
        super().save(*args, **kwargs)
        self._sync_prefix()

    def _sync_prefix(self):
        from apps.students.models import StudentSequence

        sequence = StudentSequence.objects.filter(scholarship_session_id=self.session_id).first()
        if sequence is None or sequence.last_number or sequence.certificate_last_number:
            return
        prefix = f"{self.short_name}{self.session.code}"
        if sequence.prefix != prefix:
            sequence.prefix = prefix
            sequence.save(update_fields=["prefix", "updated_at"])
