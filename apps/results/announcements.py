from apps.results.models import Winner, WinnerAnnouncement

DISMISS_COOKIE = "cgs_announcement_dismiss"
DISMISS_STORAGE_KEY = "cgs-announcement-dismissed"


def dismissal_token(announcement):
    return f"{announcement.pk}.{announcement.publication_version}"


def published_winner_queryset(session):
    if session is None:
        return Winner.objects.none()
    return (
        Winner.objects.filter(
            scholarship_session=session,
            is_published=True,
            student__deleted_at__isnull=True,
            student__is_active=True,
        )
        .select_related(
            "student",
            "student__institute",
            "student__academic_class",
            "student__category",
            "award_type",
            "scholarship_session",
        )
        .order_by("position", "award_type__display_order", "student__name_bn")
    )


def landing_announcement(session):
    """Featured announcement for the active session, only when winners are public."""
    if session is None:
        return None
    announcement = (
        WinnerAnnouncement.objects.filter(
            scholarship_session=session,
            is_published=True,
            is_featured=True,
            archived_at__isnull=True,
        )
        .select_related("scholarship_session")
        .first()
    )
    if announcement is None:
        return None
    if not published_winner_queryset(session).exists():
        return None
    return announcement


def visitor_has_dismissed(request, announcement):
    if announcement is None:
        return True
    return request.COOKIES.get(DISMISS_COOKIE) == dismissal_token(announcement)
