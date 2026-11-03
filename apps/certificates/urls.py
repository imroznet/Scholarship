from django.urls import path

from apps.certificates.views import CertificateDownloadView, CertificateIssueView

app_name = "certificates"

urlpatterns = [
    path("issue/<int:winner_id>/", CertificateIssueView.as_view(), name="issue"),
    path("<int:pk>/", CertificateDownloadView.as_view(), name="download"),
]
