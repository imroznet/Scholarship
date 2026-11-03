from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.examinations.models import Examination
from apps.results.models import AwardType, ExamResult
from apps.results.services import create_winner, save_result, set_winner_publication
from apps.schedules.services import activate_stage
from apps.verification.models import VerificationHistory
from apps.verification.services import set_verification_status
from apps.verification.statuses import VerificationStatus
from tests.helpers import ScholarshipTestCase


class VerificationTests(ScholarshipTestCase):
    def test_status_changes_are_kept_in_history(self):
        student = self.register()
        self.assertEqual(student.verification_status, VerificationStatus.PENDING)
        set_verification_status(
            student=student,
            status=VerificationStatus.CORRECTION_REQUIRED,
            remarks="ছবি স্পষ্ট নয়।",
            actor=self.admin,
        )
        set_verification_status(
            student=student,
            status=VerificationStatus.VERIFIED,
            remarks="যাচাই সম্পন্ন।",
            actor=self.admin,
        )
        student.refresh_from_db()
        self.assertEqual(student.verification_status, VerificationStatus.VERIFIED)
        history = list(VerificationHistory.objects.filter(student=student).order_by("pk"))
        self.assertEqual(
            [item.status for item in history],
            [VerificationStatus.PENDING, VerificationStatus.CORRECTION_REQUIRED, VerificationStatus.VERIFIED],
        )
        self.login("operator")
        self.assertEqual(self.client.post(reverse("verification:review", args=[student.pk]), {"status": VerificationStatus.REJECTED}).status_code, 403)
        student.refresh_from_db()
        self.assertEqual(student.verification_status, VerificationStatus.VERIFIED)


class ScheduleTests(ScholarshipTestCase):
    def _stamp(self, schedule, start, end, countdown=None):
        schedule.start_at = start
        schedule.end_at = end
        schedule.countdown_target = countdown or end
        schedule.show_countdown = True
        schedule.save()
        return schedule

    def test_only_one_stage_can_be_active_and_it_does_not_advance_itself(self):
        now = timezone.now()
        application = self._stamp(
            self.session.schedules.get(stage="APPLICATION"),
            now - timedelta(days=2),
            now - timedelta(days=1),
            now - timedelta(hours=1),
        )
        verification = self._stamp(
            self.session.schedules.get(stage="VERIFICATION"),
            now,
            now + timedelta(days=3),
        )
        activate_stage(verification)
        activate_stage(application)
        application.refresh_from_db()
        verification.refresh_from_db()
        self.assertTrue(application.is_active)
        self.assertFalse(verification.is_active)
        self.assertEqual(self.session.schedules.filter(is_active=True).count(), 1)
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, "সময়সীমা শেষ হয়েছে। পরবর্তী ঘোষণার জন্য অপেক্ষা করুন।")
        application.refresh_from_db()
        verification.refresh_from_db()
        self.assertTrue(application.is_active)
        self.assertFalse(verification.is_active)

    def test_countdown_uses_dhaka_time(self):
        now = timezone.now()
        target = timezone.make_aware(
            timezone.datetime(2026, 12, 1, 15, 30),
            timezone.get_current_timezone(),
        )
        self._stamp(
            self.session.schedules.get(stage="APPLICATION"),
            now - timedelta(hours=1),
            target,
            target,
        )
        activate_stage(self.session.schedules.get(stage="APPLICATION"))
        page = self.client.get(reverse("public:schedule"))
        self.assertContains(page, "2026-12-01T15:30:00+06:00")
        self.assertEqual(timezone.get_current_timezone_name(), "Asia/Dhaka")

    def test_stage_without_dates_cannot_be_activated(self):
        schedule = self.session.schedules.get(stage="EXAMINATION")
        with self.assertRaises(ValidationError):
            activate_stage(schedule)
        schedule.refresh_from_db()
        self.assertFalse(schedule.is_active)


class ResultAndWinnerTests(ScholarshipTestCase):
    def exam(self, **overrides):
        values = {
            "scholarship_session": self.session,
            "academic_class": self.academic_class,
            "name_bn": "মেধা পরীক্ষা",
            "exam_date": date(2026, 6, 1),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "venue": "স্কুল মাঠ",
            "total_marks": 100,
            "status": Examination.Status.DRAFT,
        }
        values.update(overrides)
        return Examination.objects.create(**values)

    def test_marks_are_validated_and_approval_is_explicit(self):
        student = self.register()
        examination = self.exam()
        with self.assertRaises(ValidationError):
            save_result(
                student=student,
                examination=examination,
                obtained_marks=Decimal("-1"),
                remarks="",
                position=None,
                status=ExamResult.Status.DRAFT,
                actor=self.admin,
            )
        with self.assertRaises(ValidationError):
            save_result(
                student=student,
                examination=examination,
                obtained_marks=Decimal("101"),
                remarks="",
                position=None,
                status=ExamResult.Status.DRAFT,
                actor=self.admin,
            )
        draft = save_result(
            student=student,
            examination=examination,
            obtained_marks=Decimal("88.50"),
            remarks="",
            position=1,
            status=ExamResult.Status.DRAFT,
            actor=self.admin,
        )
        self.assertEqual(draft.status, ExamResult.Status.DRAFT)
        approved = save_result(
            student=student,
            examination=examination,
            obtained_marks=Decimal("90"),
            remarks="ঠিক আছে",
            position=1,
            status=ExamResult.Status.APPROVED,
            actor=self.admin,
        )
        self.assertEqual(approved.pk, draft.pk)
        self.assertEqual(ExamResult.objects.count(), 1)
        self.assertEqual(approved.status, ExamResult.Status.APPROVED)
        self.assertEqual(approved.approved_by, self.admin)
        self.login("operator")
        self.assertEqual(self.client.get(reverse("results:home")).status_code, 403)

    def test_winner_publication_is_manual_and_forbidden_to_operators(self):
        student = self.register()
        award = AwardType.objects.create(name_bn="মেধাবৃত্তি", display_order=1)
        winner = create_winner(
            student=student,
            award_type=award,
            position=1,
            amount=Decimal("5000"),
            result=None,
            actor=self.admin,
        )
        self.assertFalse(winner.is_published)
        self.login("operator")
        denied = self.client.post(reverse("winners:publish", args=[winner.pk]), {"publish": "1"})
        self.assertEqual(denied.status_code, 403)
        winner.refresh_from_db()
        self.assertFalse(winner.is_published)
        hidden = self.client.get(reverse("public:winners"))
        self.assertNotContains(hidden, student.name_bn)
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        winner.refresh_from_db()
        self.assertTrue(winner.is_published)
        self.assertIsNotNone(winner.published_at)
