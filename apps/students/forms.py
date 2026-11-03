from django import forms

from apps.academics.models import AcademicClass
from apps.core.forms import BanglaFormMixin
from apps.core.models import WebsiteSetting
from apps.institutes.models import Institute


class StudentForm(BanglaFormMixin, forms.Form):
    name_bn = forms.CharField(label="নাম (বাংলা)", max_length=150)
    name_en = forms.CharField(label="নাম (ইংরেজি)", max_length=150)
    date_of_birth = forms.DateField(label="জন্ম তারিখ")
    mobile = forms.CharField(label="মোবাইল", max_length=11)
    father_name = forms.CharField(label="পিতার নাম", max_length=150, required=False)
    father_mobile = forms.CharField(label="পিতার মোবাইল", max_length=11, required=False)
    mother_name = forms.CharField(label="মাতার নাম", max_length=150, required=False)
    mother_mobile = forms.CharField(label="মাতার মোবাইল", max_length=11, required=False)
    village = forms.CharField(label="গ্রাম", max_length=120)
    post_office = forms.CharField(label="ডাকঘর", max_length=120)
    upazila = forms.CharField(label="উপজেলা", max_length=120)
    district = forms.CharField(label="জেলা", max_length=120)
    institute = forms.ModelChoiceField(label="শিক্ষা প্রতিষ্ঠান", queryset=Institute.objects.none())
    academic_class = forms.ModelChoiceField(label="শ্রেণি", queryset=AcademicClass.objects.none())
    photo = forms.FileField(label="ছবি", required=False)
    is_active = forms.BooleanField(label="সক্রিয়", required=False, initial=True)

    def __init__(self, *args, institutes, classes, include_active=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["institute"].queryset = institutes
        self.fields["academic_class"].queryset = classes
        required = WebsiteSetting.load().parent_fields_required
        for name in ("father_name", "father_mobile", "mother_name", "mother_mobile"):
            self.fields[name].required = required
        if not include_active:
            del self.fields["is_active"]
