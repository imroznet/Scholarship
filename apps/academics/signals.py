from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.academics.models import AcademicClass, ClassRegistrationSetting
from apps.sessions.models import ScholarshipSession


@receiver(post_save, sender=AcademicClass, dispatch_uid="class_registration_rows")
def create_registration_rows(sender, instance, created, **kwargs):
    if not created:
        return
    for session in ScholarshipSession.objects.all():
        ClassRegistrationSetting.objects.get_or_create(
            scholarship_session=session,
            academic_class=instance,
            defaults={"is_open": False},
        )
