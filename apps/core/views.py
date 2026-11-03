from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.core.forms import BanglaFormMixin
from apps.core.models import WebsiteSetting
from django import forms


class WebsiteSettingForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = WebsiteSetting
        fields = [
            "parent_fields_required",
            "min_student_age",
            "max_student_age",
            "max_photo_mb",
            "max_logo_mb",
            "max_attachment_mb",
            "students_per_page",
        ]
        labels = {
            "parent_fields_required": "অভিভাবকের তথ্য আবশ্যক",
            "min_student_age": "সর্বনিম্ন বয়স",
            "max_student_age": "সর্বোচ্চ বয়স",
            "max_photo_mb": "ছবির সর্বোচ্চ আকার (এমবি)",
            "max_logo_mb": "লোগোর সর্বোচ্চ আকার (এমবি)",
            "max_attachment_mb": "সংযুক্তির সর্বোচ্চ আকার (এমবি)",
            "students_per_page": "প্রতি পৃষ্ঠায় শিক্ষার্থী",
        }

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("min_student_age")
        maximum = cleaned.get("max_student_age")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error("max_student_age", "সর্বোচ্চ বয়স সর্বনিম্নের চেয়ে বড় হতে হবে।")
        return cleaned


class SettingsView(SuperAdminRequiredMixin, View):
    def get(self, request):
        form = WebsiteSettingForm(instance=WebsiteSetting.load())
        return render(request, "dashboard/simple_form.html", {"form": form, "page_title": "সেটিংস", "submit_label": "সংরক্ষণ"})

    def post(self, request):
        setting = WebsiteSetting.load()
        form = WebsiteSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            log_action(request=request, action="settings.update", instance=setting)
            messages.success(request, "সেটিংস সংরক্ষণ হয়েছে।")
            return redirect("settings:manage")
        return render(request, "dashboard/simple_form.html", {"form": form, "page_title": "সেটিংস", "submit_label": "সংরক্ষণ"})


def error_403(request, exception):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
