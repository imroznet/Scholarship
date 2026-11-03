import re

from django import forms

from apps.academics.models import AcademicClass
from apps.core.forms import BanglaFormMixin

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")


class AcademicClassForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicClass
        fields = ["name_bn", "name_en", "code", "display_order", "is_active"]
        labels = {
            "name_bn": "শ্রেণির নাম (বাংলা)",
            "name_en": "শ্রেণির নাম (ইংরেজি)",
            "code": "কোড",
            "display_order": "ক্রম",
            "is_active": "সক্রিয়",
        }

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if not CODE_RE.match(code):
            raise forms.ValidationError("শ্রেণি কোড সঠিক নয়।")
        return code
