from django.db.models import Q

from apps.students.models import Student
from apps.verification.statuses import VerificationStatus


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def filtered_students(params, user):
    include_deleted = user.is_super_admin and params.get("deleted") == "1"
    if include_deleted:
        queryset = Student.objects.filter(deleted_at__isnull=False)
    else:
        queryset = Student.objects.alive()
        if not user.is_super_admin:
            queryset = queryset.filter(is_active=True)
    queryset = queryset.select_related(
        "institute",
        "category",
        "academic_class",
        "scholarship_session",
        "registered_by",
    )
    query = (params.get("q") or "").strip()
    if query:
        queryset = queryset.filter(
            Q(student_id__icontains=query)
            | Q(name_bn__icontains=query)
            | Q(name_en__icontains=query)
            | Q(mobile__icontains=query)
        )
    institute_id = _int(params.get("institute"))
    if institute_id:
        queryset = queryset.filter(institute_id=institute_id)
    class_id = _int(params.get("academic_class"))
    if class_id:
        queryset = queryset.filter(academic_class_id=class_id)
    category_id = _int(params.get("category"))
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    session_id = _int(params.get("session"))
    if session_id:
        queryset = queryset.filter(scholarship_session_id=session_id)
    status = params.get("verification_status") or ""
    if status in VerificationStatus.values:
        queryset = queryset.filter(verification_status=status)
    return queryset.order_by("-created_at", "student_id")
