from django.urls import reverse

from apps.academics.models import AcademicClass, ClassRegistrationSetting
from apps.institutes.models import Institute
from apps.students.services import find_duplicate_warnings
from tests.helpers import ScholarshipTestCase


class InstituteAndClassTests(ScholarshipTestCase):
    def test_super_admin_creates_institute_and_category_is_stored_on_the_institute(self):
        self.login()
        response = self.client.post(
            reverse("institutes:create"),
            {
                "name_bn": "দারুল উলুম",
                "name_en": "Darul Ulum",
                "institute_code": "dul",
                "category": self.madrasa.pk,
                "district": "চাঁদপুর",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("institutes:list"))
        institute = Institute.objects.get(institute_code="DUL")
        self.assertEqual(institute.category, self.madrasa)

    def test_operator_cannot_change_categories_or_classes(self):
        self.login("operator")
        self.assertEqual(self.client.get(reverse("institutes:categories")).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("academics:class_create"),
                {"name_bn": "নবম", "name_en": "Nine", "code": "C9", "display_order": 2, "is_active": "on"},
            ).status_code,
            403,
        )
        self.assertFalse(AcademicClass.objects.filter(code="C9").exists())

    def test_class_creation_and_registration_open_close(self):
        self.login()
        created = self.client.post(
            reverse("academics:class_create"),
            {"name_bn": "নবম", "name_en": "Class 9", "code": "C9", "display_order": 2, "is_active": "on"},
        )
        self.assertRedirects(created, reverse("academics:classes"))
        academic_class = AcademicClass.objects.get(code="C9")
        setting = ClassRegistrationSetting.objects.get(
            scholarship_session=self.session,
            academic_class=academic_class,
        )
        self.assertFalse(setting.is_open)
        opened = self.client.post(
            reverse("academics:registration"),
            {"session": self.session.pk, "action": "open", "class_ids": [academic_class.pk]},
        )
        self.assertEqual(opened.status_code, 302)
        setting.refresh_from_db()
        self.assertTrue(setting.is_currently_open())
        closed = self.client.post(
            reverse("academics:registration"),
            {"session": self.session.pk, "action": "close", "class_ids": [academic_class.pk]},
        )
        self.assertEqual(closed.status_code, 302)
        setting.refresh_from_db()
        self.assertFalse(setting.is_currently_open())
        self.assertEqual(self.client.get(reverse("students:list")).status_code, 200)

    def test_duplicate_warning_does_not_use_parent_phone_alone_as_a_block(self):
        self.register()
        warnings = find_duplicate_warnings(
            name_bn="অন্য নাম",
            name_en="Other Name",
            date_of_birth=self.student_data()["date_of_birth"],
            mobile="01722222222",
            father_mobile="01811111111",
            institute=self.institute,
        )
        self.assertTrue(any("অভিভাবকের মোবাইল" in item for item in warnings))
        second = self.register(name_bn="অন্য নাম", name_en="Other Name", mobile="01722222222")
        self.assertNotEqual(second.student_id, self.session.students.get(name_bn="রাহিমা খাতুন").student_id)
