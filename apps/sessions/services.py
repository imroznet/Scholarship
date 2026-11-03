from django.db import transaction

from apps.sessions.models import ScholarshipSession


def ensure_session_dependencies(session):
    from apps.academics.models import AcademicClass, ClassRegistrationSetting
    from apps.branding.defaults import initial_branding_kwargs
    from apps.branding.models import ScholarshipBranding
    from apps.schedules.models import Schedule
    from apps.students.models import StudentSequence

    branding, _created = ScholarshipBranding.objects.get_or_create(
        session=session,
        defaults=initial_branding_kwargs(session),
    )
    prefix = f"{branding.short_name.upper()}{session.code}"
    StudentSequence.objects.get_or_create(
        scholarship_session=session,
        defaults={"prefix": prefix, "last_number": 0, "certificate_last_number": 0},
    )
    for order, stage in enumerate(Schedule.Stage, start=1):
        Schedule.objects.get_or_create(
            scholarship_session=session,
            stage=stage.value,
            defaults={
                "title_bn": stage.label,
                "display_order": order,
                "is_active": False,
                "show_countdown": True,
            },
        )
    for academic_class in AcademicClass.objects.all():
        ClassRegistrationSetting.objects.get_or_create(
            scholarship_session=session,
            academic_class=academic_class,
            defaults={"is_open": False},
        )


def set_active_session(session):
    with transaction.atomic():
        list(ScholarshipSession.objects.select_for_update().values_list("pk", flat=True))
        ScholarshipSession.objects.exclude(pk=session.pk).update(is_active=False)
        ScholarshipSession.objects.filter(pk=session.pk).update(is_active=True)
        session.is_active = True
