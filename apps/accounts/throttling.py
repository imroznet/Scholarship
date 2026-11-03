from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import LoginAttempt


def client_ip(request):
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def _window_start():
    return timezone.now() - timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)


def is_login_locked(username, ip_address):
    return (
        LoginAttempt.objects.filter(
            username=username.strip().lower(),
            ip_address=ip_address,
            successful=False,
            attempted_at__gte=_window_start(),
        ).count()
        >= settings.LOGIN_FAILURE_LIMIT
    )


def record_failed_login(username, ip_address):
    LoginAttempt.objects.create(
        username=username.strip().lower()[:150],
        ip_address=ip_address,
        successful=False,
    )
    cutoff = timezone.now() - timedelta(days=2)
    LoginAttempt.objects.filter(attempted_at__lt=cutoff).delete()


def clear_login_failures(username, ip_address):
    LoginAttempt.objects.filter(
        username=username.strip().lower(),
        ip_address=ip_address,
        successful=False,
    ).delete()
