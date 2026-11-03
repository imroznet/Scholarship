from django.db.models import Count, Q

from apps.institutes.models import Institute
from apps.results.models import Winner
from apps.students.models import Student
from apps.verification.statuses import VerificationStatus


def dashboard_stats(session):
    students = Student.objects.alive()
    if session is None:
        students = students.none()
    else:
        students = students.filter(scholarship_session=session)
    totals = students.aggregate(
        total=Count("id"),
        verified=Count("id", filter=Q(verification_status=VerificationStatus.VERIFIED)),
        pending=Count("id", filter=Q(verification_status=VerificationStatus.PENDING)),
        rejected=Count("id", filter=Q(verification_status=VerificationStatus.REJECTED)),
        correction=Count("id", filter=Q(verification_status=VerificationStatus.CORRECTION_REQUIRED)),
    )
    by_category = list(students.values("category__name_bn").annotate(total=Count("id")).order_by("category__name_bn"))
    by_class = list(
        students.values("academic_class__name_bn")
        .annotate(total=Count("id"))
        .order_by("academic_class__display_order", "academic_class__name_bn")
    )
    published_winners = 0
    if session is not None:
        published_winners = Winner.objects.filter(scholarship_session=session, is_published=True).count()
    return {
        **totals,
        "by_category": by_category,
        "by_class": by_class,
        "published_winners": published_winners,
        "institutes": Institute.objects.filter(is_active=True).count(),
    }
