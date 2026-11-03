from django import template
from django.utils import timezone

from apps.schedules.countdown import split_remaining

register = template.Library()

BANGLA_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MONTHS = [
    "জানুয়ারি",
    "ফেব্রুয়ারি",
    "মার্চ",
    "এপ্রিল",
    "মে",
    "জুন",
    "জুলাই",
    "আগস্ট",
    "সেপ্টেম্বর",
    "অক্টোবর",
    "নভেম্বর",
    "ডিসেম্বর",
]


@register.filter
def bangla_digits(value):
    return "" if value is None else str(value).translate(BANGLA_DIGITS)


@register.filter
def bangla_pad(value, width=2):
    try:
        text = str(int(value)).zfill(int(width))
    except (TypeError, ValueError):
        return ""
    return text.translate(BANGLA_DIGITS)


@register.filter
def is_past(value):
    if not value:
        return False
    moment = value
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, timezone.get_current_timezone())
    return moment <= timezone.now()


@register.filter
def lines(value):
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


@register.filter
def bangla_date(value):
    if not value:
        return ""
    if hasattr(value, "tzinfo") and timezone.is_aware(value):
        value = timezone.localtime(value)
    text = f"{value.day} {MONTHS[value.month - 1]} {value.year}"
    if hasattr(value, "hour"):
        text += f", {value.hour:02d}:{value.minute:02d}"
    return text.translate(BANGLA_DIGITS)


@register.simple_tag
def countdown_state(schedule):
    if schedule is None or not schedule.show_countdown or not schedule.countdown_target:
        return None
    return split_remaining(schedule.countdown_target, timezone.now())


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
