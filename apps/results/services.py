from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action
from apps.results.models import ExamResult, Winner


def save_result(*, student, examination, obtained_marks, remarks, position, status, actor, request=None):
    if student.deleted_at:
        raise ValidationError("মুছে ফেলা শিক্ষার্থীর ফলাফল দেওয়া যাবে না।")
    if student.scholarship_session_id != examination.scholarship_session_id:
        raise ValidationError("শিক্ষার্থী এই সেশনের নয়।")
    if student.academic_class_id != examination.academic_class_id:
        raise ValidationError("শিক্ষার্থীর শ্রেণি পরীক্ষার শ্রেণির সাথে মিলছে না।")
    if status not in ExamResult.Status.values:
        raise ValidationError("অবৈধ ফলাফল অবস্থা।")
    obtained = Decimal(obtained_marks)
    total = Decimal(examination.total_marks)
    if obtained < 0 or obtained > total:
        raise ValidationError("নম্বর ঋণাত্মক বা মোট নম্বরের বেশি হতে পারবে না।")
    with transaction.atomic():
        existing = (
            ExamResult.objects.select_for_update()
            .filter(student=student, examination=examination)
            .first()
        )
        before = None
        if existing:
            before = {
                "obtained_marks": str(existing.obtained_marks),
                "status": existing.status,
                "position": existing.position,
                "remarks": existing.remarks,
            }
            result = existing
        else:
            result = ExamResult(student=student, examination=examination, entered_by=actor)
        result.obtained_marks = obtained
        result.total_marks = total
        result.remarks = (remarks or "").strip()
        result.position = position
        result.status = status
        if status == ExamResult.Status.APPROVED:
            result.approved_by = actor
            result.approved_at = timezone.now()
        else:
            result.approved_by = None
            result.approved_at = None
        result.full_clean()
        result.save()
        log_action(
            request=request,
            action="result.save",
            instance=result,
            changes={"before": before, "after": {"obtained_marks": str(obtained), "status": status, "position": position}},
        )
        return result


def create_winner(*, student, award_type, position, amount, result, actor, request=None):
    if student.deleted_at or not student.is_active:
        raise ValidationError("নিষ্ক্রিয় বা মুছে ফেলা শিক্ষার্থীকে বিজয়ী করা যাবে না।")
    winner = Winner(
        student=student,
        scholarship_session=student.scholarship_session,
        award_type=award_type,
        position=position,
        scholarship_amount=amount,
        result_reference=result,
        is_published=False,
        published_at=None,
        created_by=actor,
    )
    winner.full_clean()
    winner.save()
    log_action(request=request, action="winner.create", instance=winner, changes={"published": False})
    return winner


def set_winner_publication(*, winner, publish, actor, request=None):
    with transaction.atomic():
        winner = Winner.objects.select_for_update().select_related("student").get(pk=winner.pk)
        if winner.student.scholarship_session_id != winner.scholarship_session_id:
            raise ValidationError("শিক্ষার্থী এই স্কলারশিপ সেশনের নয়।")
        if winner.student.deleted_at:
            raise ValidationError("মুছে ফেলা শিক্ষার্থীর বিজয় প্রকাশ করা যাবে না।")
        winner.is_published = bool(publish)
        winner.published_at = timezone.now() if publish else None
        winner.save(update_fields=["is_published", "published_at", "updated_at"])
        log_action(
            request=request,
            action="winner.publish" if publish else "winner.unpublish",
            instance=winner,
            changes={"is_published": winner.is_published},
        )
        return winner
