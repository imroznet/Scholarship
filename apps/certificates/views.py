from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.certificates.models import Certificate
from apps.certificates.pdf import render_certificate_pdf
from apps.certificates.services import issue_certificate
from apps.results.models import Winner


class CertificateIssueView(SuperAdminRequiredMixin, View):
    def post(self, request, winner_id):
        winner = get_object_or_404(
            Winner.objects.select_related("student", "scholarship_session"),
            pk=winner_id,
        )
        try:
            certificate = issue_certificate(winner, request.user, request=request)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
            return redirect("winners:list")
        return redirect("certificates:download", pk=certificate.pk)


class CertificateDownloadView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        certificate = get_object_or_404(
            Certificate.objects.select_related(
                "winner__student__institute",
                "winner__student__academic_class",
                "winner__student__category",
                "winner__award_type",
                "scholarship_session__branding",
            ),
            pk=pk,
        )
        payload = render_certificate_pdf(certificate)
        disposition = "attachment" if request.GET.get("download") == "1" else "inline"
        response = HttpResponse(payload, content_type="application/pdf")
        response["Content-Disposition"] = f'{disposition}; filename="{certificate.certificate_number}.pdf"'
        response["X-Content-Type-Options"] = "nosniff"
        return response
