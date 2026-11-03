import re

from django import forms

from apps.core.forms import BanglaFormMixin
from apps.sessions.models import ScholarshipSession

CODE_RE = re.compile(r"^[A-Za-z0-9]{2,10}$")


class SessionForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = ScholarshipSession
        fields = ["name_bn", "name_en", "code", "start_date", "end_date", "description", "is_active"]
        labels = {
            "name_bn": "সেশনের নাম (বাংলা)",
            "name_en": "সেশনের নাম (ইংরেজি)",
            "code": "সেশন কোড",
            "start_date": "শুরুর তারিখ",
            "end_date": "শেষ তারিখ",
            "description": "বিবরণ",
            "is_active": "সক্রিয় সেশন",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.students.exists():
            self.fields["code"].disabled = True

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not CODE_RE.match(code):
            raise forms.ValidationError("সেশন কোড ২ থেকে ১০টি ইংরেজি অক্ষর বা সংখ্যা হবে।")
        return code

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "শেষ তারিখ শুরুর তারিখের পরে হতে হবে।")
        return cleaned
