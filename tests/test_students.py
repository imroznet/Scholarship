import threading
from datetime import date

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.test import TransactionTestCase
from django.urls import reverse

from apps.institutes.models import Institute
from apps.students.models import Student
from apps.students.services import allocate_student_id, soft_delete_student, update_student
from tests.helpers import ScholarshipDataMixin, ScholarshipTestCase, uploaded


class StudentTests(ScholarshipTestCase):
    def test_valid_registration_assigns_session_category_and_sequential_id(self):
        student = self.register()
        self.assertEqual(student.student_id, "CGS26-0001")
        self.assertEqual(student.category, self.general)
        self.assertEqual(student.category_name_bn, "সাধারণ")
        self.assertEqual(student.scholarship_session, self.session)
        second = self.register(name_bn="করিম মিয়া", name_en="Karim Mia", mobile="01733333333")
        self.assertEqual(second.student_id, "CGS26-0002")

    def test_invalid_mobile_and_closed_class_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.register(mobile="12345")
        self.session.class_registrations.update(is_open=False)
        with self.assertRaises(ValidationError):
            self.register(mobile="01744444444", name_en="Closed Class")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(self.session.student_sequence.last_number, 0)

    def test_failed_registration_rolls_back_the_sequence(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                allocate_student_id(self.session)
                raise RuntimeError("registration failed")
        self.session.student_sequence.refresh_from_db()
        self.assertEqual(self.session.student_sequence.last_number, 0)
        student = self.register()
        self.assertEqual(student.student_id, "CGS26-0001")

    def test_category_is_snapshotted_and_updates_only_when_the_institute_changes(self):
        student = self.register()
        self.institute.category = self.madrasa
        self.institute.save(update_fields=["category", "updated_at"])
        student.refresh_from_db()
        self.assertEqual(student.category, self.general)
        self.assertEqual(student.category_name_bn, "সাধারণ")
        other = Institute.objects.create(
            name_bn="মাদ্রাসা ইবতেদায়ি",
            institute_code="MIB",
            category=self.madrasa,
            is_active=True,
        )
        update_student(
            student=student,
            actor=self.admin,
            cleaned=self.student_data(institute=other),
        )
        student.refresh_from_db()
        self.assertEqual(student.category, self.madrasa)
        self.assertEqual(student.category_name_bn, "মাদ্রাসা")

    def test_photo_upload_edit_soft_delete_and_http_success_page(self):
        self.login("operator")
        payload = self.form_data()
        payload["photo"] = uploaded()
        response = self.client.post(reverse("students:create"), payload)
        student = Student.objects.get()
        self.assertRedirects(response, reverse("students:registered", args=[student.pk]))
        page = self.client.get(response["Location"])
        self.assertContains(page, "সফলভাবে শিক্ষার্থী নিবন্ধন সম্পন্ন হয়েছে।")
        self.assertContains(page, student.student_id)
        self.assertContains(page, "রাহিমা খাতুন")
        self.assertContains(page, self.institute.name_bn)
        self.assertContains(page, self.academic_class.name_bn)
        photo = self.client.get(reverse("students:photo", args=[student.pk]))
        self.assertEqual(photo.status_code, 200)
        self.assertIn("image/", photo["Content-Type"])
        edited = self.client.post(
            reverse("students:edit", args=[student.pk]),
            self.form_data(name_en="Rahima Updated"),
        )
        self.assertRedirects(edited, reverse("students:detail", args=[student.pk]))
        student.refresh_from_db()
        self.assertEqual(student.name_en, "Rahima Updated")
        denied = self.client.post(reverse("students:delete", args=[student.pk]))
        self.assertEqual(denied.status_code, 403)
        self.assertIsNone(student.deleted_at)
        soft_delete_student(student=student, actor=self.admin)
        student.refresh_from_db()
        self.assertIsNotNone(student.deleted_at)
        self.assertFalse(student.is_active)
        listed = self.client.get(reverse("students:list"))
        self.assertNotContains(listed, student.student_id)
        nxt = self.register(name_bn="নতুন শিক্ষার্থী", name_en="New Student", mobile="01755555555")
        self.assertEqual(nxt.student_id, "CGS26-0002")
        self.assertNotEqual(nxt.student_id, student.student_id)

    def test_duplicate_confirmation_and_search(self):
        self.login("operator")
        first_payload = self.form_data()
        first_payload["photo"] = uploaded()
        first = self.client.post(reverse("students:create"), first_payload)
        self.assertEqual(first.status_code, 302)
        warned_payload = self.form_data(name_en="Rahima Two")
        warned_payload["photo"] = uploaded("second.png")
        warned = self.client.post(reverse("students:create"), warned_payload)
        self.assertEqual(warned.status_code, 200)
        self.assertContains(warned, "একই নাম")
        self.assertEqual(Student.objects.count(), 1)
        confirmed_payload = self.form_data(name_en="Rahima Two", confirm_duplicates="1")
        confirmed_payload["photo"] = uploaded("third.png")
        confirmed = self.client.post(reverse("students:create"), confirmed_payload)
        self.assertEqual(confirmed.status_code, 302)
        self.assertEqual(Student.objects.count(), 2)
        found = self.client.get(reverse("students:list"), {"q": "01711111111"})
        self.assertContains(found, "CGS26-0001")
        by_class = self.client.get(reverse("students:list"), {"academic_class": self.academic_class.pk})
        self.assertContains(by_class, "রাহিমা খাতুন")

    def test_private_photo_is_not_public(self):
        student = self.register()
        self.client.logout()
        response = self.client.get(reverse("students:photo", args=[student.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(f"/media/{student.photo.name}").status_code, 404)


class ConcurrentIdTests(ScholarshipDataMixin, TransactionTestCase):
    def test_parallel_registration_keeps_unique_ids(self):
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def work(name_en, mobile):
            try:
                connection.close()
                barrier.wait(timeout=15)
                student = self.register(name_en=name_en, mobile=mobile, name_bn=name_en)
                results.append(student.student_id)
            except Exception as exc:  # noqa: BLE001 - the assertion reports the thread error
                errors.append(repr(exc))
            finally:
                connection.close()

        threads = [
            threading.Thread(target=work, args=("Student One", "01710000001")),
            threading.Thread(target=work, args=("Student Two", "01710000002")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertFalse(errors, errors)
        self.assertEqual(sorted(results), ["CGS26-0001", "CGS26-0002"])
        self.assertEqual(Student.objects.count(), 2)
        self.session.student_sequence.refresh_from_db()
        self.assertEqual(self.session.student_sequence.last_number, 2)
