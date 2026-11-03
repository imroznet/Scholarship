from django.conf import settings
from django.db import models


class Certificate(models.Model):
    winner = models.OneToOneField("results.Winner", on_delete=models.PROTECT, related_name="certificate")
    scholarship_session = models.ForeignKey(
        "scholarship_sessions.ScholarshipSession",
        on_delete=models.PROTECT,
        related_name="certificates",
    )
    certificate_number = models.CharField(max_length=40, unique=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_certificates",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.certificate_number
