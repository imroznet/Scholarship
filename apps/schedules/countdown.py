from django.utils import timezone


def split_remaining(target, now):
    """Split a timezone-aware target into days, hours, minutes and seconds.

    Naive or missing timestamps return None so callers can show a safe message
    instead of a misleading timer.
    """
    if target is None or now is None:
        return None
    if timezone.is_naive(target) or timezone.is_naive(now):
        return None
    seconds = int((target - now).total_seconds())
    if seconds <= 0:
        return {"finished": True, "days": 0, "hours": 0, "minutes": 0, "seconds": 0}
    return {
        "finished": False,
        "days": seconds // 86400,
        "hours": (seconds % 86400) // 3600,
        "minutes": (seconds % 3600) // 60,
        "seconds": seconds % 60,
    }
