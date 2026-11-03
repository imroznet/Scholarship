from apps.sessions.models import ScholarshipSession


def get_active_session():
    return (
        ScholarshipSession.objects.filter(is_active=True)
        .select_related("branding")
        .first()
    )
