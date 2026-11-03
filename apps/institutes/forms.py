import re

from django import forms
from django.db.models import Q

from apps.core.forms import BanglaFormMixin
from apps.institutes.models import Category, Institute

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{2,20}$")


class CategoryForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name_bn", "name_en", "code", "is_active"]
        labels = {
            "name_bn": "বিভাগের নাম (বাংলা)",
            "name_en": "বিভাগের নাম (ইংরেজি)",
            "code": "কোড",
            "is_active": "সক্রিয়",
        }

    def clean_code(self):
        code = self.cleaned_data["code"].strip().lower()
        if not CODE_RE.match(code):
            raise forms.ValidationError("কোড ২–২০ অক্ষরের হতে হবে।")
        return code


class InstituteForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = Institute
        fields = [
            "name_bn",
            "name_en",
            "institute_code",
            "category",
            "address",
            "village",
            "post_office",
            "upazila",
            "district",
            "is_active",
        ]
        labels = {
            "name_bn": "প্রতিষ্ঠানের নাম (বাংলা)",
            "name_en": "প্রতিষ্ঠানের নাম (ইংরেজি)",
            "institute_code": "প্রতিষ্ঠান কোড",
            "category": "বিভাগ",
            "address": "ঠিকানা",
            "village": "গ্রাম",
            "post_office": "ডাকঘর",
            "upazila": "উপজেলা",
            "district": "জেলা",
            "is_active": "সক্রিয়",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_filter = Q(is_active=True)
        if self.instance.pk and self.instance.category_id:
            category_filter |= Q(pk=self.instance.category_id)
        self.fields["category"].queryset = Category.objects.filter(category_filter)

    def clean_institute_code(self):
        code = self.cleaned_data["institute_code"].strip().upper()
        if not CODE_RE.match(code):
            raise forms.ValidationError("প্রতিষ্ঠান কোড ২–২০ অক্ষরের হতে হবে।")
        return code
