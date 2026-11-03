from django import forms

from apps.academics.models import AcademicClass
from apps.core.forms import BanglaFormMixin
from apps.examinations.models import Examination
from apps.sessions.models import ScholarshipSession


class ExaminationForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = Examination
        fields = [
            "scholarship_session",
            "academic_class",
            "name_bn",
            "exam_date",
            "start_time",
            "end_time",
            "venue",
            "instructions",
            "total_marks",
            "status",
        ]
        labels = {
            "scholarship_session": "সেশন",
            "academic_class": "শ্রেণি",
            "name_bn": "পরীক্ষার নাম",
            "exam_date": "তারিখ",
            "start_time": "শুরু",
            "end_time": "শেষ",
            "venue": "স্থান",
            "instructions": "নির্দেশনা",
            "total_marks": "মোট নম্বর",
            "status": "অবস্থা",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scholarship_session"].queryset = ScholarshipSession.objects.order_by("-start_date")
        self.fields["academic_class"].queryset = AcademicClass.objects.filter(is_active=True)
