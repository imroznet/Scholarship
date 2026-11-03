from django import forms

from apps.core.forms import BanglaFormMixin
from apps.results.models import AwardType, Winner
from apps.students.models import Student


class AwardTypeForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = AwardType
        fields = ["name_bn", "name_en", "display_order", "is_active"]
        labels = {
            "name_bn": "পুরস্কারের নাম",
            "name_en": "ইংরেজি নাম",
            "display_order": "ক্রম",
            "is_active": "সক্রিয়",
        }


class WinnerForm(BanglaFormMixin, forms.Form):
    student = forms.ModelChoiceField(label="শিক্ষার্থী", queryset=Student.objects.none())
    award_type = forms.ModelChoiceField(label="পুরস্কার", queryset=AwardType.objects.none())
    position = forms.IntegerField(label="অবস্থান", required=False, min_value=1)
    scholarship_amount = forms.DecimalField(label="টাকার পরিমাণ", required=False, min_value=0, decimal_places=2, max_digits=10)
    result_reference = forms.IntegerField(label="ফলাফল রেফারেন্স", required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = (
            Student.objects.alive().filter(is_active=True).select_related("scholarship_session").order_by("student_id")
        )
        self.fields["award_type"].queryset = AwardType.objects.filter(is_active=True)
        self.fields["student"].label_from_instance = lambda obj: f"{obj.student_id} — {obj.name_bn}"
