from django import forms

from apps.core.forms import BanglaFormMixin
from apps.schedules.models import Schedule


class ScheduleForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = Schedule
        fields = [
            "title_bn",
            "description_bn",
            "start_at",
            "end_at",
            "countdown_target",
            "display_order",
            "show_countdown",
        ]
        labels = {
            "title_bn": "শিরোনাম",
            "description_bn": "বিবরণ",
            "start_at": "শুরু",
            "end_at": "শেষ",
            "countdown_target": "কাউন্টডাউনের লক্ষ্য সময়",
            "display_order": "ক্রম",
            "show_countdown": "কাউন্টডাউন দেখাবে",
        }
