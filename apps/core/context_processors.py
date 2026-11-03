from django.db.utils import DatabaseError


def site_context(request):
    try:
        from apps.sessions.selectors import get_active_session

        session = get_active_session()
    except DatabaseError:
        session = None
    branding = None
    if session is not None:
        branding = getattr(session, "branding", None)
    return {"active_session": session, "branding": branding}
