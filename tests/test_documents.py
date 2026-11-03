from io import BytesIO
from unittest.mock import patch

from django.urls import reverse
from openpyxl import load_workbook

from apps.certificates.pdf import bangla_image_has_ink, render_bangla_image, render_certificate_pdf
from apps.certificates.services import issue_certificate
from apps.reports.exporters import sanitize_spreadsheet
from apps.results.models import AwardType
from apps.results.services import create_winner, set_winner_publication
from tests.helpers import ScholarshipTestCase


class CertificateTests(ScholarshipTestCase):
    def winner(self, student, award_name="মেধাবৃত্তি"):
        award = AwardType.objects.create(name_bn=award_name)
        return create_winner(
            student=student,
            award_type=award,
            position=1,
            amount=None,
            result=None,
            actor=self.admin,
        )

    def test_pdf_uses_session_branding_bangla_and_a_unique_number(self):
        self.assertTrue(bangla_image_has_ink("কান্ট্রি গ্রুপ স্কলারশিপ"))
        student = self.register()
        self.session.branding.name_bn = "সেশন একের স্কলারশিপ"
        self.session.branding.sponsor_name_bn = "সেশন একের স্পনসর"
        self.session.branding.certificate_title_bn = "সম্মাননা সনদ"
        self.session.branding.save()
        winner = self.winner(student)
        set_winner_publication(winner=winner, publish=True, actor=self.admin)
        seen = []
        real = render_bangla_image

        def spy(text, *args, **kwargs):
            seen.append(text)
            return real(text, *args, **kwargs)

        with patch("apps.certificates.pdf.render_bangla_image", side_effect=spy):
            first = issue_certificate(winner, self.admin)
            again = issue_certificate(winner, self.admin)
            payload = render_certificate_pdf(first)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(first.certificate_number, "CGS26-CERT-0001")
        self.assertEqual(first.scholarship_session, self.session)
        self.assertTrue(payload.startswith(b"%PDF"))
        self.assertIn(first.certificate_number.encode(), payload)
        self.assertIn(student.student_id.encode(), payload)
        self.assertIn("সেশন একের স্কলারশিপ", seen)
        self.assertIn("সেশন একের স্পনসর", seen)
        self.assertIn(student.name_bn, seen)
        other = self.register(name_bn="দ্বিতীয় শিক্ষার্থী", name_en="Second Student", mobile="01766666666")
        second = issue_certificate(self.winner(other, "বিশেষ বৃত্তি"), self.admin)
        self.assertEqual(second.certificate_number, "CGS26-CERT-0002")
        self.login("operator")
        self.assertEqual(self.client.get(reverse("certificates:download", args=[first.pk])).status_code, 403)

    def test_certificate_keeps_the_session_it_was_issued_for(self):
        from datetime import date

        from apps.sessions.models import ScholarshipSession
        from apps.sessions.services import set_active_session

        student = self.register()
        self.session.branding.name_bn = "২০২৬ সনদের নাম"
        self.session.branding.save()
        certificate = issue_certificate(self.winner(student), self.admin)
        later = ScholarshipSession.objects.create(
            name_bn="২০২৭ সেশন",
            code="27",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 12, 31),
            is_active=False,
        )
        later.branding.name_bn = "২০২৭ সনদের নাম"
        later.branding.save()
        set_active_session(later)
        seen = []

        def spy(text, *args, **kwargs):
            seen.append(text)
            return render_bangla_image(text, *args, **kwargs)

        with patch("apps.certificates.pdf.render_bangla_image", side_effect=spy):
            render_certificate_pdf(certificate)
        self.assertIn("২০২৬ সনদের নাম", seen)
        self.assertNotIn("২০২৭ সনদের নাম", seen)


class ExportTests(ScholarshipTestCase):
    def test_spreadsheet_values_are_sanitized(self):
        self.assertEqual(sanitize_spreadsheet("=1+1"), "'=1+1")
        self.assertEqual(sanitize_spreadsheet("+880"), "'+880")
        self.assertEqual(sanitize_spreadsheet("-1"), "'-1")
        self.assertEqual(sanitize_spreadsheet("@cmd"), "'@cmd")
        self.assertEqual(sanitize_spreadsheet("রাহিমা"), "রাহিমা")

    def test_csv_and_xlsx_exports_respect_permissions_and_unicode(self):
        student = self.register(name_bn="=রাহিমা", name_en="Rahima", father_name="গোপনপিতা")
        self.login("operator")
        denied = self.client.get(reverse("reports:winners_csv"))
        self.assertEqual(denied.status_code, 403)
        csv_response = self.client.get(reverse("reports:students_csv"))
        self.assertEqual(csv_response.status_code, 200)
        text = csv_response.content.decode("utf-8-sig")
        self.assertTrue(csv_response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn("রাহিমা", text)
        self.assertIn("'=রাহিমা", text)
        self.assertNotIn("গোপনপিতা", text)
        self.assertNotIn("জন্ম তারিখ", text)
        xlsx_response = self.client.get(reverse("reports:students_xlsx"))
        sheet = load_workbook(BytesIO(xlsx_response.content)).active
        headers = [cell.value for cell in sheet[1]]
        self.assertIn("নাম (বাংলা)", headers)
        self.assertNotIn("পিতার নাম", headers)
        self.assertEqual(sheet.cell(2, headers.index("নাম (বাংলা)") + 1).value, "'=রাহিমা")
        self.login("admin")
        admin_csv = self.client.get(reverse("reports:students_csv")).content.decode("utf-8-sig")
        self.assertIn("গোপনপিতা", admin_csv)
        self.assertIn(student.student_id, admin_csv)
        award = AwardType.objects.create(name_bn="তৃতীয় স্থান")
        create_winner(student=student, award_type=award, position=3, amount=None, result=None, actor=self.admin)
        winner_sheet = load_workbook(
            BytesIO(self.client.get(reverse("reports:winners_xlsx")).content)
        ).active
        values = [cell.value for row in winner_sheet.iter_rows() for cell in row]
        self.assertIn(student.student_id, values)
        self.assertNotIn(student.mobile, values)
        self.assertNotIn("গোপনপিতা", values)
