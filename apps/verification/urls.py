from django.urls import path

from apps.verification.views import VerificationListView, VerificationPrintView, VerificationReviewView

app_name = "verification"

urlpatterns = [
    path("", VerificationListView.as_view(), name="list"),
    path("print/", VerificationPrintView.as_view(), name="print"),
    path("<int:pk>/", VerificationReviewView.as_view(), name="review"),
]
