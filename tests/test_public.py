from datetime import timedelta

from django.utils import timezone
from django.urls import reverse

from apps.examinations.models import Examination
from apps.notices.models import Notice
from apps.results.models import AwardType
from apps.results.services import create_winner, set_winner_publication
from tests.helpers import ScholarshipTestCase


class PublicSiteTests(ScholarshipTestCase):
    def test_homepage_is_bangla_and_uses_database_branding(self):
        branding = self.session.branding
        branding.name_bn = "পরীক্ষামূলক স্কলারশিপ শিরোনাম"
        branding.sponsor_name_bn = "পরীক্ষামূলক স্পনসর"
        branding.objectives_bn = "মেধাবী শিক্ষার্থীকে সহায়তা"
        branding.save()
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, 'lang="bn"')
        self.assertContains(page, "পরীক্ষামূলক স্কলারশিপ শিরোনাম")
        self.assertContains(page, "পরীক্ষামূলক স্পনসর")
        self.assertContains(page, "অনলাইন আবেদন গ্রহণ করা হয় না")
        self.assertNotContains(page, "<form")
        process = self.client.get(reverse("public:process"))
        self.assertContains(process, "অনলাইন আবেদন গ্রহণ করা হয় না")
        self.assertNotContains(process, 'type="submit"')

    def test_only_published_notices_are_visible(self):
        now = timezone.now()
        Notice.objects.create(
            scholarship_session=self.session,
            title_bn="খসড়া নোটিশ",
            slug="draft-notice",
            content_bn="এটি খসড়া।",
            status=Notice.Status.DRAFT,
            created_by=self.admin,
        )
        Notice.objects.create(
            scholarship_session=self.session,
            title_bn="মেয়াদোত্তীর্ণ নোটিশ",
            slug="expired-notice",
            content_bn="পুরনো তথ্য।",
            status=Notice.Status.PUBLISHED,
            published_at=now - timedelta(days=5),
            expires_at=now - timedelta(days=1),
            created_by=self.admin,
        )
        live = Notice.objects.create(
            scholarship_session=self.session,
            title_bn="প্রকাশিত নোটিশ",
            slug="প্রকাশিত-নোটিশ",
            content_bn="সবাইকে জানানো যাচ্ছে।",
            status=Notice.Status.PUBLISHED,
            published_at=now - timedelta(hours=1),
            created_by=self.admin,
        )
        listing = self.client.get(reverse("public:notices"))
        self.assertContains(listing, live.title_bn)
        self.assertNotContains(listing, "খসড়া নোটিশ")
        self.assertNotContains(listing, "মেয়াদোত্তীর্ণ নোটিশ")
        detail = self.client.get(reverse("public:notice_detail", args=[live.slug]))
        self.assertContains(detail, "সবাইকে জানানো যাচ্ছে।")
        missing = self.client.get(reverse("public:notice_detail", args=["draft-notice"]))
        self.assertEqual(missing.status_code, 404)

    def test_published_winners_hide_private_fields(self):
        student = self.register()
        award = AwardType.objects.create(name_bn="প্রথম স্থান")
        winner = create_winner(
            student=student,
            award_type=award,
            position=1,
            amount=None,
            result=None,
            actor=self.admin,
        )
        before = self.client.get(reverse("public:winners"))
        self.assertNotContains(before, student.student_id)
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        page = self.client.get(reverse("public:winners"))
        self.assertContains(page, student.name_bn)
        self.assertContains(page, student.student_id)
        self.assertContains(page, self.institute.name_bn)
        self.assertContains(page, self.academic_class.name_bn)
        self.assertContains(page, "সাধারণ")
        self.assertContains(page, "প্রথম স্থান")
        self.assertNotContains(page, student.mobile)
        self.assertNotContains(page, student.father_name)
        self.assertNotContains(page, student.mother_name)
        self.assertNotContains(page, student.village)
        self.assertNotContains(page, student.date_of_birth.isoformat())
        photo = self.client.get(reverse("public:winner_photo", args=[winner.pk]))
        self.assertEqual(photo.status_code, 200)
        self.assertIn("image/", photo["Content-Type"])

    def test_unpublished_exam_is_hidden_and_robots_blocks_private_paths(self):
        Examination.objects.create(
            scholarship_session=self.session,
            academic_class=self.academic_class,
            name_bn="অপ্রকাশিত পরীক্ষা",
            exam_date=timezone.localdate(),
            start_time=timezone.datetime.strptime("10:00", "%H:%M").time(),
            end_time=timezone.datetime.strptime("11:00", "%H:%M").time(),
            venue="গোপন কক্ষ",
            total_marks=50,
            status=Examination.Status.DRAFT,
        )
        home = self.client.get(reverse("public:home"))
        self.assertNotContains(home, "অপ্রকাশিত পরীক্ষা")
        robots = self.client.get(reverse("public:robots"))
        self.assertContains(robots, "Disallow: /dashboard/")
        self.assertContains(robots, "Disallow: /media/")
