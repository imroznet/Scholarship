from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action
from apps.students.models import Student
from apps.verification.models import VerificationHistory
from apps.verification.statuses import VerificationStatus


def set_verification_status(*, student, status, remarks, actor, request=None):
    if status not in VerificationStatus.values:
        raise ValidationError("অবৈধ যাচাই অবস্থা।")
    with transaction.atomic():
        student = Student.objects.select_for_update().get(pk=student.pk)
        if student.deleted_at:
            raise ValidationError("মুছে ফেলা রেকর্ড যাচাই করা যাবে না।")
        previous = student.verification_status
        student.verification_status = status
        student.save(update_fields=["verification_status", "updated_at"])
        history = VerificationHistory.objects.create(
            student=student,
            status=status,
            remarks=(remarks or "").strip(),
            verified_by=actor,
            verified_at=timezone.now(),
        )
        log_action(
            request=request,
            action="verification.update",
            instance=history,
            changes={"from": previous, "to": status, "remarks": history.remarks, "student_id": student.student_id},
        )
        return history
