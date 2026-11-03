from django import forms

from apps.branding.models import ScholarshipBranding
from apps.core.forms import BanglaFormMixin


class BrandingForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = ScholarshipBranding
        fields = [
            "name_bn",
            "name_en",
            "short_name",
            "slogan_bn",
            "description_bn",
            "about_bn",
            "objectives_bn",
            "eligibility_bn",
            "application_process_bn",
            "contact_info",
            "email",
            "phone",
            "address",
            "sponsor_name_bn",
            "sponsor_name_en",
            "sponsor_description",
            "sponsor_website",
            "sponsor_contact",
            "certificate_title_bn",
            "certificate_footer_bn",
            "signatory_name_bn",
            "signatory_title_bn",
        ]
        labels = {
            "name_bn": "স্কলারশিপের নাম (বাংলা)",
            "name_en": "স্কলারশিপের নাম (ইংরেজি)",
            "short_name": "সংক্ষিপ্ত নাম",
            "slogan_bn": "স্লোগান",
            "description_bn": "সংক্ষিপ্ত পরিচিতি",
            "about_bn": "বিস্তারিত পরিচিতি",
            "objectives_bn": "উদ্দেশ্য (প্রতি লাইনে একটি)",
            "eligibility_bn": "যোগ্যতা (প্রতি লাইনে একটি)",
            "application_process_bn": "আবেদন প্রক্রিয়া (প্রতি লাইনে একটি)",
            "contact_info": "যোগাযোগের তথ্য",
            "email": "ইমেইল",
            "phone": "ফোন",
            "address": "ঠিকানা",
            "sponsor_name_bn": "স্পনসরের নাম (বাংলা)",
            "sponsor_name_en": "স্পনসরের নাম (ইংরেজি)",
            "sponsor_description": "স্পনসরের বিবরণ",
            "sponsor_website": "স্পনসরের ওয়েবসাইট",
            "sponsor_contact": "স্পনসরের যোগাযোগ",
            "certificate_title_bn": "সনদের শিরোনাম",
            "certificate_footer_bn": "সনদের ফুটার",
            "signatory_name_bn": "স্বাক্ষরকারীর নাম",
            "signatory_title_bn": "স্বাক্ষরকারীর পদবি",
        }
        widgets = {
            "about_bn": forms.Textarea(attrs={"rows": 5}),
            "objectives_bn": forms.Textarea(attrs={"rows": 5}),
            "eligibility_bn": forms.Textarea(attrs={"rows": 4}),
            "application_process_bn": forms.Textarea(attrs={"rows": 5}),
            "description_bn": forms.Textarea(attrs={"rows": 3}),
            "sponsor_description": forms.Textarea(attrs={"rows": 3}),
            "certificate_footer_bn": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_short_name(self):
        value = (self.cleaned_data.get("short_name") or "").strip().upper()
        if not value.isalpha() or not 2 <= len(value) <= 10:
            raise forms.ValidationError("সংক্ষিপ্ত নাম ২ থেকে ১০টি ইংরেজি অক্ষর হবে।")
        return value
