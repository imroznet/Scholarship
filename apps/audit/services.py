from datetime import date, datetime
from decimal import Decimal

from django.db import models

from apps.audit.models import AuditLog


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, models.Model):
        return str(value.pk)
    return value


def log_action(*, request=None, action, instance=None, changes=None, target_model="", target_id="", target_repr=""):
    user = None
    ip_address = None
    user_agent = ""
    if request is not None:
        current = getattr(request, "user", None)
        if current is not None and current.is_authenticated:
            user = current
        ip_address = request.META.get("REMOTE_ADDR") or None
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:255]
    if instance is not None:
        target_model = instance._meta.label
        target_id = "" if instance.pk is None else str(instance.pk)
        target_repr = str(instance)[:255]
    return AuditLog.objects.create(
        user=user,
        action=action[:64],
        target_model=target_model[:100],
        target_id=target_id[:64],
        target_repr=target_repr[:255],
        changes=json_safe(changes or {}),
        ip_address=ip_address,
        user_agent=user_agent,
    )
