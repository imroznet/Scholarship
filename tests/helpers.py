import tempfile
from datetime import date
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.academics.models import AcademicClass, ClassRegistrationSetting
from apps.accounts.models import User
from apps.institutes.models import Category, Institute
from apps.sessions.models import ScholarshipSession
from apps.students.services import register_student


def png_bytes(size=(64, 64), color=(15, 61, 46)):
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def photo_content(name="student.png"):
    return ContentFile(png_bytes(), name=name)


def uploaded(name="photo.png", content_type="image/png", payload=None):
    return SimpleUploadedFile(name, payload if payload is not None else png_bytes(), content_type=content_type)


class ScholarshipDataMixin:
    """Shared records for TestCase and TransactionTestCase suites."""
    password = "Scholar-Admin-2026!"

    def setUp(self):
        super().setUp()
        self.media_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()
        self._reset_storage()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", self.password)
        self.operator = User.objects.create_user("operator", "operator@example.com", self.password)
        self.general = Category.objects.create(name_bn="সাধারণ", name_en="General", code="general")
        self.madrasa = Category.objects.create(name_bn="মাদ্রাসা", name_en="Madrasa", code="madrasa")
        self.academic_class = AcademicClass.objects.create(
            name_bn="অষ্টম",
            name_en="Class 8",
            code="C8",
            display_order=1,
        )
        self.session = ScholarshipSession.objects.create(
            name_bn="কান্ট্রি গ্রুপ স্কলারশিপ - ২০২৬",
            name_en="Country Group Scholarship - 2026",
            code="26",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            is_active=True,
            description="পরীক্ষামূলক সেশন",
        )
        self.institute = Institute.objects.create(
            name_bn="আদর্শ উচ্চ বিদ্যালয়",
            name_en="Adarsha High School",
            institute_code="AHS",
            category=self.general,
            district="ঢাকা",
            is_active=True,
        )
        setting = ClassRegistrationSetting.objects.get(
            scholarship_session=self.session,
            academic_class=self.academic_class,
        )
        setting.is_open = True
        setting.save(update_fields=["is_open", "updated_at"])

    def tearDown(self):
        self.settings_override.disable()
        self._reset_storage()
        self.media_dir.cleanup()
        super().tearDown()

    def _reset_storage(self):
        default_storage.__dict__.pop("base_location", None)
        default_storage.__dict__.pop("location", None)

    def login(self, who="admin"):
        self.client.force_login(self.admin if who == "admin" else self.operator)

    def student_data(self, **overrides):
        data = {
            "name_bn": "রাহিমা খাতুন",
            "name_en": "Rahima Khatun",
            "date_of_birth": date(2012, 5, 2),
            "mobile": "01711111111",
            "father_name": "করিম উদ্দিন",
            "father_mobile": "01811111111",
            "mother_name": "জরিমা বেগম",
            "mother_mobile": "01911111111",
            "village": "পূর্বপাড়া",
            "post_office": "মডেল",
            "upazila": "সাভার",
            "district": "ঢাকা",
            "institute": self.institute,
            "academic_class": self.academic_class,
        }
        data.update(overrides)
        return data

    def register(self, actor=None, **overrides):
        return register_student(
            actor=actor or self.operator,
            photo=photo_content(),
            cleaned=self.student_data(**overrides),
            request=None,
        )

    def form_data(self, **overrides):
        payload = {
            "name_bn": "রাহিমা খাতুন",
            "name_en": "Rahima Khatun",
            "date_of_birth": "02/05/2012",
            "mobile": "01711111111",
            "father_name": "করিম উদ্দিন",
            "father_mobile": "01811111111",
            "mother_name": "জরিমা বেগম",
            "mother_mobile": "01911111111",
            "village": "পূর্বপাড়া",
            "post_office": "মডেল",
            "upazila": "সাভার",
            "district": "ঢাকা",
            "institute": str(self.institute.pk),
            "academic_class": str(self.academic_class.pk),
        }
        payload.update(overrides)
        return payload


class ScholarshipTestCase(ScholarshipDataMixin, TestCase):
    pass
