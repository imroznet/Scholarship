from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.sessions.models import ScholarshipSession
from apps.sessions.services import ensure_session_dependencies


@receiver(post_save, sender=ScholarshipSession, dispatch_uid="session_dependencies")
def create_session_dependencies(sender, instance, created, **kwargs):
    if created:
        ensure_session_dependencies(instance)
