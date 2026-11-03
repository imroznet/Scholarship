from datetime import date, timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import AcademicClass
from apps.institutes.models import Institute
from apps.results.announcements import DISMISS_COOKIE, dismissal_token
from apps.results.models import AwardType, WinnerAnnouncement
from apps.results.services import create_winner, set_winner_publication
from apps.schedules.countdown import split_remaining
from apps.schedules.services import activate_stage
from apps.sessions.models import ScholarshipSession
from apps.students.forms import DEFAULT_DISTRICT, DEFAULT_UPAZILA, StudentForm
from apps.students.models import Student
from tests.helpers import ScholarshipTestCase


class LocationDefaultTests(ScholarshipTestCase):
    def test_new_registration_shows_sakhipur_and_tangail(self):
        self.login()
        page = self.client.get(reverse("students:create"))
        self.assertContains(page, f'value="{DEFAULT_UPAZILA}"')
        self.assertContains(page, f'value="{DEFAULT_DISTRICT}"')

    def test_blank_location_fields_use_defaults_and_overrides_win(self):
        blank = StudentForm(
            self.form_data(upazila="  ", district=""),
            institutes=Institute.objects.all(),
            classes=AcademicClass.objects.all(),
        )
        self.assertTrue(blank.is_valid(), blank.errors)
        self.assertEqual(blank.cleaned_data["upazila"], DEFAULT_UPAZILA)
        self.assertEqual(blank.cleaned_data["district"], DEFAULT_DISTRICT)

        chosen = StudentForm(
            self.form_data(upazila="মধুপুর", district="ঢাকা"),
            institutes=Institute.objects.all(),
            classes=AcademicClass.objects.all(),
        )
        self.assertTrue(chosen.is_valid(), chosen.errors)
        self.assertEqual(chosen.cleaned_data["upazila"], "মধুপুর")
        self.assertEqual(chosen.cleaned_data["district"], "ঢাকা")

    def test_failed_submission_keeps_entered_location(self):
        form = StudentForm(
            self.form_data(date_of_birth="32/13/2012", upazila="কালিহাতী", district="টাঙ্গাইল"),
            institutes=Institute.objects.all(),
            classes=AcademicClass.objects.all(),
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form["upazila"].value(), "কালিহাতী")
        self.assertEqual(form["district"].value(), "টাঙ্গাইল")

    def test_editing_keeps_saved_location_and_does_not_rewrite_other_students(self):
        student = self.register(upazila="সাভার", district="ঢাকা")
        other = self.register(
            name_bn="করিম মিয়া",
            name_en="Karim Mia",
            mobile="01733333333",
            father_mobile="01833333333",
            upazila="ঘাটাইল",
            district="টাঙ্গাইল",
        )
        form = StudentForm(
            self.form_data(upazila="", district=""),
            institutes=Institute.objects.all(),
            classes=AcademicClass.objects.all(),
            existing_student=student,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["upazila"], "সাভার")
        self.assertEqual(form.cleaned_data["district"], "ঢাকা")

        self.login()
        response = self.client.post(reverse("students:edit", args=[student.pk]), self.form_data(upazila="", district=""))
        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(student.upazila, "সাভার")
        self.assertEqual(student.district, "ঢাকা")
        self.assertEqual(other.upazila, "ঘাটাইল")
        self.assertEqual(other.district, "টাঙ্গাইল")
        self.assertEqual(Student.objects.filter(upazila=DEFAULT_UPAZILA).count(), 0)


class CountdownTests(ScholarshipTestCase):
    def _activate(self, target, show=True):
        now = timezone.now()
        schedule = self.session.schedules.get(stage="EXAMINATION")
        schedule.start_at = now - timedelta(hours=1)
        schedule.end_at = now + timedelta(days=10)
        schedule.countdown_target = target
        schedule.show_countdown = show
        schedule.title_bn = "মেধা পরীক্ষা"
        schedule.description_bn = "পরীক্ষার সময়সূচি"
        schedule.save()
        activate_stage(schedule)
        return schedule

    def test_future_countdown_uses_the_database_target(self):
        now = timezone.now()
        target = now + timedelta(days=2, hours=3, minutes=4, seconds=5)
        parts = split_remaining(target, now)
        self.assertEqual(parts["days"], 2)
        self.assertEqual(parts["hours"], 3)
        self.assertEqual(parts["minutes"], 4)
        self.assertEqual(parts["seconds"], 5)
        self.assertFalse(parts["finished"])
        schedule = self._activate(target)
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, "দিন")
        self.assertContains(page, "ঘণ্টা")
        self.assertContains(page, "মিনিট")
        self.assertContains(page, "সেকেন্ড")
        self.assertContains(page, "data-countdown-target")
        local_target = timezone.localtime(schedule.countdown_target)
        self.assertContains(page, local_target.strftime("%Y-%m-%dT%H:%M:%S"))
        self.assertContains(page, "+06:00")
        self.assertContains(page, "মেধা পরীক্ষা")
        self.assertContains(page, "পরীক্ষার সময়সূচি")

    def test_expired_countdown_shows_completed_state(self):
        self._activate(timezone.now() - timedelta(minutes=5))
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, "সময়সীমা শেষ হয়েছে। পরবর্তী ঘোষণার জন্য অপেক্ষা করুন।")
        self.assertNotContains(page, "data-countdown-target")

    def test_missing_countdown_is_not_rendered(self):
        self._activate(None, show=False)
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, "মেধা পরীক্ষা")
        self.assertNotContains(page, "data-countdown")

    def test_invalid_timestamp_is_rejected(self):
        naive = timezone.datetime(2026, 12, 1, 15, 30)
        self.assertIsNone(split_remaining(naive, timezone.now()))
        self.assertIsNone(split_remaining(None, timezone.now()))
        aware = timezone.now() + timedelta(seconds=30)
        self.assertIsNone(split_remaining(aware, naive))


class WinnerAnnouncementTests(ScholarshipTestCase):
    def publish_winner(self, **overrides):
        student = self.register(**overrides)
        award = AwardType.objects.create(name_bn=overrides.get("award_name", "প্রথম স্থান"), display_order=1)
        winner = create_winner(
            student=student,
            award_type=award,
            position=1,
            amount=None,
            result=None,
            actor=self.admin,
        )
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        return student, winner

    def test_active_announcement_is_server_rendered_and_can_be_dismissed_per_browser(self):
        student, winner = self.publish_winner()
        announcement = WinnerAnnouncement.objects.get(scholarship_session=self.session)
        self.assertTrue(announcement.is_published)
        self.assertTrue(announcement.is_featured)
        self.assertIsNotNone(announcement.published_at)
        home = self.client.get(reverse("public:home"), follow=False)
        self.assertEqual(home.status_code, 302)
        self.assertEqual(home.url, reverse("public:announcement"))
        page = self.client.get(reverse("public:announcement"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, student.name_bn)
        self.assertContains(page, student.student_id)
        self.assertContains(page, self.institute.name_bn)
        self.assertContains(page, "মূল ওয়েবসাইটে প্রবেশ করুন")
        self.assertNotContains(page, student.mobile)
        self.assertContains(page, self.session.branding.name_bn)
        direct_home = self.client.get(reverse("public:home") + "?home=1")
        self.assertEqual(direct_home.status_code, 200)
        self.assertContains(direct_home, "অনলাইন আবেদন গ্রহণ করা হয় না")
        dismissed = self.client.get(reverse("public:announcement_dismiss"), follow=False)
        self.assertEqual(dismissed.status_code, 302)
        self.assertEqual(self.client.cookies[DISMISS_COOKIE].value, dismissal_token(announcement))
        after = self.client.get(reverse("public:home"))
        self.assertEqual(after.status_code, 200)
        self.assertContains(after, "অনলাইন আবেদন গ্রহণ করা হয় না")
        stranger = Client()
        self.assertEqual(stranger.get(reverse("public:home"), follow=False).status_code, 302)
        again = self.client.get(reverse("public:announcement"))
        self.assertContains(again, student.name_bn)
        winner.refresh_from_db()
        self.assertTrue(winner.is_published)

    def test_unpublished_and_archived_announcements_are_not_the_landing_page(self):
        student = self.register()
        award = AwardType.objects.create(name_bn="বিশেষ পুরস্কার")
        winner = create_winner(
            student=student,
            award_type=award,
            position=2,
            amount=None,
            result=None,
            actor=self.admin,
        )
        hidden = self.client.get(reverse("public:announcement"))
        self.assertNotContains(hidden, student.student_id)
        self.assertEqual(self.client.get(reverse("public:home"), follow=False).status_code, 200)
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        self.login()
        archived = self.client.post(reverse("winners:announcement"), {"action": "archive"})
        self.assertEqual(archived.status_code, 302)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("public:home"), follow=False).status_code, 200)
        landing = self.client.get(reverse("public:announcement"))
        self.assertNotContains(landing, student.student_id)
        history = self.client.get(reverse("public:announcement_session", args=[self.session.code]))
        self.assertContains(history, student.name_bn)
        self.login("operator")
        self.assertEqual(self.client.post(reverse("winners:announcement"), {"action": "feature"}).status_code, 403)

    def test_past_session_announcement_survives_a_new_featured_announcement(self):
        student = self.register()
        old = ScholarshipSession.objects.create(
            name_bn="আগের সেশন",
            name_en="Previous Session",
            code="25",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            is_active=False,
        )
        student.scholarship_session = old
        student.save(update_fields=["scholarship_session", "updated_at"])
        award = AwardType.objects.create(name_bn="আগের পুরস্কার")
        winner = create_winner(
            student=student,
            award_type=award,
            position=1,
            amount=None,
            result=None,
            actor=self.admin,
        )
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        current_student, _current_winner = self.publish_winner(
            name_bn="নতুন বিজয়ী",
            name_en="New Winner",
            mobile="01755555555",
            award_name="নতুন পুরস্কার",
        )
        past = self.client.get(reverse("public:announcement_session", args=["25"]))
        self.assertContains(past, student.name_bn)
        self.assertContains(past, "আগের সেশন")
        self.assertNotContains(past, current_student.name_bn)
        current = self.client.get(reverse("public:announcement"))
        self.assertContains(current, current_student.name_bn)
        self.assertNotContains(current, student.student_id)

    def test_a_new_publication_version_is_shown_after_an_earlier_dismissal(self):
        student, _winner = self.publish_winner()
        announcement = WinnerAnnouncement.objects.get()
        self.client.get(reverse("public:announcement_dismiss"))
        self.assertEqual(self.client.get(reverse("public:home"), follow=False).status_code, 200)
        self.login()
        self.client.post(reverse("winners:announcement"), {"action": "archive"})
        self.client.post(reverse("winners:announcement"), {"action": "feature"})
        self.client.logout()
        announcement.refresh_from_db()
        self.assertGreater(announcement.publication_version, 1)
        self.assertEqual(self.client.get(reverse("public:home"), follow=False).status_code, 302)
        self.assertContains(self.client.get(reverse("public:announcement")), student.name_bn)


class ResponsiveMarkupTests(ScholarshipTestCase):
    def test_public_and_dashboard_layouts_include_mobile_structures(self):
        now = timezone.now()
        schedule = self.session.schedules.get(stage="APPLICATION")
        schedule.start_at = now - timedelta(hours=1)
        schedule.end_at = now + timedelta(days=2)
        schedule.countdown_target = now + timedelta(days=1)
        schedule.show_countdown = True
        schedule.save()
        activate_stage(schedule)
        home = self.client.get(reverse("public:home"))
        self.assertContains(home, "public-menu")
        self.assertContains(home, "aria-controls=\"public-nav\"")
        self.assertContains(home, "data-countdown-part")
        self.assertContains(home, "sm:grid-cols-2")
        self.assertContains(home, "lg:text-[2.625rem]")
        self.login()
        students = self.client.get(reverse("students:list"))
        self.assertContains(students, "dashboard-nav")
        self.assertContains(students, "md:hidden")
        self.assertContains(students, "aria-controls=\"dashboard-nav\"")
        form = self.client.get(reverse("students:create"))
        self.assertContains(form, "w-full sm:w-auto")
