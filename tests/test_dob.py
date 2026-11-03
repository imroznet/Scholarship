import subprocess
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import AcademicClass
from apps.core.models import WebsiteSetting
from apps.institutes.models import Institute
from apps.students.forms import DOB_INPUT_FORMAT, StudentForm
from apps.students.models import Student
from tests.helpers import ScholarshipTestCase, uploaded


class DobMaskScriptTests(SimpleTestCase):
    def test_slash_insertion_editing_and_paste(self):
        script = Path(__file__).resolve().parent / "dob_mask_check.js"
        completed = subprocess.run(
            ["node", str(script)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("dob mask ok", completed.stdout)


class DateOfBirthFormTests(ScholarshipTestCase):
    def form(self, data=None, initial=None):
        kwargs = {
            "institutes": Institute.objects.all(),
            "classes": AcademicClass.objects.all(),
        }
        if data is not None:
            return StudentForm(data, initial=initial, **kwargs)
        return StudentForm(initial=initial, **kwargs)

    def test_valid_input_parses_as_day_month_year(self):
        form = self.form(self.form_data(date_of_birth="15/08/2012"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["date_of_birth"], date(2012, 8, 15))
        self.assertEqual(form.cleaned_data["date_of_birth"].strftime(DOB_INPUT_FORMAT), "15/08/2012")
        self.assertIsInstance(form.cleaned_data["date_of_birth"], date)

    def test_invalid_calendar_dates_are_rejected_and_keep_the_typed_value(self):
        for typed in ("31/02/2012", "29/02/2011", "00/01/2012", "15/13/2012", "2012-08-15"):
            form = self.form(self.form_data(date_of_birth=typed))
            self.assertFalse(form.is_valid(), typed)
            self.assertIn("date_of_birth", form.errors)
            rendered = str(form["date_of_birth"])
            self.assertIn(f'value="{typed}"', rendered)
            self.assertIn('type="text"', rendered)
            self.assertNotIn('type="date"', rendered)

    def test_leap_day_is_accepted(self):
        form = self.form(self.form_data(date_of_birth="29/02/2012"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["date_of_birth"], date(2012, 2, 29))

    def test_future_date_is_rejected(self):
        today = timezone.localdate()
        future = date(today.year + 1, 1, 1)
        typed = future.strftime(DOB_INPUT_FORMAT)
        form = self.form(self.form_data(date_of_birth=typed))
        self.assertFalse(form.is_valid())
        self.assertIn("অতীতের হতে হবে", form.errors["date_of_birth"][0])
        self.assertIn(f'value="{typed}"', str(form["date_of_birth"]))

    def test_widget_is_a_numeric_text_input_with_placeholder(self):
        rendered = str(self.form()["date_of_birth"])
        self.assertIn('type="text"', rendered)
        self.assertIn('placeholder="DD/MM/YYYY"', rendered)
        self.assertIn('inputmode="numeric"', rendered)
        self.assertIn('data-dob-mask="1"', rendered)
        self.assertIn("id_date_of_birth_helptext", rendered)

    def test_edit_form_displays_existing_date_as_day_month_year(self):
        student = self.register()
        self.login("operator")
        page = self.client.get(reverse("students:edit", args=[student.pk]))
        self.assertContains(page, 'value="02/05/2012"')
        self.assertContains(page, 'placeholder="DD/MM/YYYY"')
        self.assertContains(page, 'inputmode="numeric"')
        self.assertContains(page, "dob-input.js")

    def test_edit_validation_error_preserves_typed_value_and_does_not_change_the_record(self):
        student = self.register()
        self.login("operator")
        payload = self.form_data(date_of_birth="31/02/2012")
        response = self.client.post(reverse("students:edit", args=[student.pk]), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="31/02/2012"')
        self.assertContains(response, "জন্ম তারিখ সঠিক নয়")
        student.refresh_from_db()
        self.assertEqual(student.date_of_birth, date(2012, 5, 2))

    def test_registration_stores_a_normal_date(self):
        self.login("operator")
        payload = self.form_data(date_of_birth="15/08/2012")
        payload["photo"] = uploaded()
        response = self.client.post(reverse("students:create"), payload)
        student = Student.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(student.date_of_birth, date(2012, 8, 15))
        self.assertEqual(Student._meta.get_field("date_of_birth").get_internal_type(), "DateField")

    def test_existing_age_limits_still_apply(self):
        settings_obj = WebsiteSetting.load()
        today = timezone.localdate()
        too_young = date(today.year - 1, 6, 15)
        too_old = date(today.year - (settings_obj.max_student_age + 5), 1, 15)
        for born in (too_young, too_old):
            with self.assertRaises(ValidationError) as caught:
                self.register(date_of_birth=born, mobile="01788888888", name_en=f"Age {born.year}")
            self.assertIn("date_of_birth", caught.exception.message_dict)
            self.assertIn("বয়স", caught.exception.message_dict["date_of_birth"][0])
        self.assertEqual(Student.objects.count(), 0)
