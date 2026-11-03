from django.conf import settings
from django.db import models

from apps.verification.statuses import VerificationStatus


class VerificationHistory(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="verification_history",
    )
    status = models.CharField(max_length=32, choices=VerificationStatus.choices)
    remarks = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verification_actions",
    )
    verified_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student_id} {self.status}"
