from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit.services import log_action
from apps.certificates.models import Certificate
from apps.results.models import Winner
from apps.sessions.models import ScholarshipSession
from apps.students.models import StudentSequence
from apps.students.services import increment_sequence_field


def allocate_certificate_number(session):
    ScholarshipSession.objects.select_for_update().get(pk=session.pk)
    sequence = StudentSequence.objects.select_for_update().get(scholarship_session=session)
    number = increment_sequence_field(sequence.pk, "certificate_last_number")
    return f"{sequence.prefix}-CERT-{number:04d}"


def issue_certificate(winner, actor, request=None):
    if winner.student.deleted_at:
        raise ValidationError("মুছে ফেলা শিক্ষার্থীর সনদ তৈরি করা যাবে না।")
    if winner.student.scholarship_session_id != winner.scholarship_session_id:
        raise ValidationError("শিক্ষার্থী এই স্কলারশিপ সেশনের নয়।")
    with transaction.atomic():
        winner = Winner.objects.select_for_update().get(pk=winner.pk)
        existing = Certificate.objects.filter(winner=winner).first()
        if existing:
            return existing
        certificate = Certificate.objects.create(
            winner=winner,
            scholarship_session=winner.scholarship_session,
            certificate_number=allocate_certificate_number(winner.scholarship_session),
            generated_by=actor,
        )
        log_action(request=request, action="certificate.issue", instance=certificate)
        return certificate
