from datetime import date

from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.branding.defaults import DEFAULT_SPONSOR_NAME_BN, DEFAULT_SPONSOR_NAME_EN
from apps.branding.services import apply_brand_images, reset_branding
from apps.core.models import WebsiteSetting
from apps.core.uploads import process_image
from apps.sessions.models import ScholarshipSession
from apps.sessions.services import set_active_session
from tests.helpers import ScholarshipTestCase, png_bytes, uploaded


class BrandingTests(ScholarshipTestCase):
    def test_session_creates_identity_and_only_one_session_is_active(self):
        branding = self.session.branding
        self.assertEqual(branding.name_bn, "কান্ট্রি গ্রুপ স্কলারশিপ - ২০২৬")
        self.assertEqual(branding.short_name, "CGS")
        later = ScholarshipSession.objects.create(
            name_bn="পরের সেশন",
            name_en="Later",
            code="27",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 12, 31),
            is_active=False,
        )
        set_active_session(later)
        set_active_session(self.session)
        self.session.refresh_from_db()
        later.refresh_from_db()
        self.assertTrue(self.session.is_active)
        self.assertFalse(later.is_active)
        self.assertEqual(ScholarshipSession.objects.filter(is_active=True).count(), 1)

    def test_sponsor_update_is_independent_of_scholarship_name(self):
        branding = self.session.branding
        branding.name_bn = "স্কলারশিপ শিরোনাম"
        branding.sponsor_name_bn = "নতুন স্পনসর"
        branding.sponsor_name_en = "New Sponsor"
        branding.save()
        branding.refresh_from_db()
        self.assertEqual(branding.name_bn, "স্কলারশিপ শিরোনাম")
        self.assertEqual(branding.sponsor_name_bn, "নতুন স্পনসর")

    def test_logo_upload_replacement_and_svg_rejection(self):
        branding = self.session.branding
        limit = WebsiteSetting.load().max_logo_mb * 1024 * 1024
        apply_brand_images(branding, {"logo": uploaded("logo.png")}, max_bytes=limit)
        branding.refresh_from_db()
        first_name = branding.logo.name
        self.assertTrue(first_name)
        apply_brand_images(branding, {"logo": uploaded("logo-two.png", payload=png_bytes(color=(30, 90, 40)))}, max_bytes=limit)
        branding.refresh_from_db()
        self.assertNotEqual(branding.logo.name, first_name)
        self.assertTrue(branding.logo_original.name)
        svg = uploaded("mark.svg", content_type="image/svg+xml", payload=b"<svg xmlns='http://www.w3.org/2000/svg'/>")
        with self.assertRaises(ValidationError):
            process_image(svg, max_bytes=limit, max_px=256)

    def test_historical_session_branding_stays_when_another_session_is_active(self):
        self.session.branding.name_bn = "২০২৬ পরিচিতি"
        self.session.branding.sponsor_name_bn = "স্পনসর ২০২৬"
        self.session.branding.save()
        later = ScholarshipSession.objects.create(
            name_bn="২০২৭ পরিচিতি",
            code="27",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 12, 31),
            is_active=False,
        )
        later.branding.name_bn = "২০২৭ পরিচিতি"
        later.branding.sponsor_name_bn = "স্পনসর ২০২৭"
        later.branding.save()
        set_active_session(later)
        self.session.branding.refresh_from_db()
        self.assertEqual(self.session.branding.name_bn, "২০২৬ পরিচিতি")
        self.assertEqual(self.session.branding.sponsor_name_bn, "স্পনসর ২০২৬")
        self.login()
        page = self.client.get(reverse("public:home"))
        self.assertContains(page, "২০২৭ পরিচিতি")
        self.assertNotContains(page, "২০২৬ পরিচিতি")

    def test_reset_restores_defaults_and_keeps_issued_prefix(self):
        student = self.register()
        branding = self.session.branding
        branding.sponsor_name_bn = "অস্থায়ী স্পনসর"
        branding.short_name = "ZZZ"
        branding.save()
        reset_branding(branding)
        branding.refresh_from_db()
        self.session.student_sequence.refresh_from_db()
        self.assertEqual(branding.sponsor_name_bn, DEFAULT_SPONSOR_NAME_BN)
        self.assertEqual(branding.sponsor_name_en, DEFAULT_SPONSOR_NAME_EN)
        self.assertEqual(branding.short_name, "ZZZ")
        self.assertEqual(self.session.student_sequence.prefix, "CGS26")
        self.assertTrue(student.student_id.startswith("CGS26-"))

    def test_operator_cannot_post_branding_changes(self):
        self.login("operator")
        response = self.client.post(
            reverse("branding:manage"),
            {"session": self.session.pk, "name_bn": "বদল", "short_name": "CGS"},
        )
        self.assertEqual(response.status_code, 403)
        self.session.branding.refresh_from_db()
        self.assertNotEqual(self.session.branding.name_bn, "বদল")

    def test_dashboard_branding_page_saves_identity(self):
        self.login()
        response = self.client.post(
            reverse("branding:manage"),
            {
                "session": self.session.pk,
                "name_bn": "হালনাগাদ নাম",
                "name_en": "Updated Name",
                "short_name": "CGS",
                "sponsor_name_bn": "কান্ট্রি গ্রুপ",
                "sponsor_name_en": "Country Group",
                "email": "office@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.session.branding.refresh_from_db()
        self.assertEqual(self.session.branding.name_bn, "হালনাগাদ নাম")
        self.assertEqual(self.session.branding.sponsor_name_en, "Country Group")
