from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.academics.models import AcademicClass
from apps.core.forms import BanglaFormMixin
from apps.core.models import WebsiteSetting
from apps.institutes.models import Institute

DOB_INPUT_FORMAT = "%d/%m/%Y"


class DayMonthYearInput(forms.TextInput):
    input_type = "text"

    def __init__(self, attrs=None):
        defaults = {
            "placeholder": "DD/MM/YYYY",
            "inputmode": "numeric",
            "autocomplete": "bday",
            "maxlength": "10",
            "spellcheck": "false",
            "autocapitalize": "off",
            "data-dob-mask": "1",
            "aria-describedby": "id_date_of_birth_helptext",
        }
        if attrs:
            defaults.update(attrs)
        super().__init__(attrs=defaults)

    def format_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value.strftime(DOB_INPUT_FORMAT)
        return str(value)


class DayMonthYearField(forms.Field):
    widget = DayMonthYearInput
    default_error_messages = {
        "invalid": "জন্ম তারিখ সঠিক নয়। DD/MM/YYYY ফরম্যাটে দিন।",
        "future": "জন্ম তারিখ অতীতের হতে হবে।",
    }

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(str(value).strip(), DOB_INPUT_FORMAT).date()
        except ValueError as exc:
            raise ValidationError(self.error_messages["invalid"], code="invalid") from exc

    def clean(self, value):
        cleaned = super().clean(value)
        if cleaned is not None and cleaned >= timezone.localdate():
            raise ValidationError(self.error_messages["future"], code="future")
        return cleaned


class StudentForm(BanglaFormMixin, forms.Form):
    name_bn = forms.CharField(label="নাম (বাংলা)", max_length=150)
    name_en = forms.CharField(label="নাম (ইংরেজি)", max_length=150)
    date_of_birth = DayMonthYearField(
        label="জন্ম তারিখ",
        help_text="দিন/মাস/বছর। উদাহরণ: 15/08/2012",
    )
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
        self.fields["date_of_birth"].error_messages["invalid"] = DayMonthYearField.default_error_messages["invalid"]
        self.fields["date_of_birth"].error_messages["future"] = DayMonthYearField.default_error_messages["future"]
        if not include_active:
            del self.fields["is_active"]
