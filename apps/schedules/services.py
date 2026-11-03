from django.core.exceptions import ValidationError
from django.db import transaction

from apps.schedules.models import Schedule


def activate_stage(schedule):
    """Activate one stage. Stages never change automatically when a countdown ends."""
    with transaction.atomic():
        current = Schedule.objects.select_for_update().get(pk=schedule.pk)
        if not current.start_at or not current.end_at:
            raise ValidationError("শুরু ও শেষ সময় না দিয়ে পর্যায় সক্রিয় করা যাবে না।")
        (
            Schedule.objects.filter(scholarship_session_id=current.scholarship_session_id)
            .exclude(pk=current.pk)
            .update(is_active=False)
        )
        Schedule.objects.filter(pk=current.pk).update(is_active=True)
        schedule.is_active = True


def deactivate_stage(schedule):
    Schedule.objects.filter(pk=schedule.pk).update(is_active=False)
    schedule.is_active = False
