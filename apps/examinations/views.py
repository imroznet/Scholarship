from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.examinations.forms import ExaminationForm
from apps.examinations.models import Examination
from apps.sessions.selectors import get_active_session


class ExaminationListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        exams = Examination.objects.select_related("scholarship_session", "academic_class")
        return render(request, "examinations/list.html", {"exams": exams, "page_title": "পরীক্ষা ব্যবস্থাপনা"})


class ExaminationCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        session = get_active_session()
        form = ExaminationForm(initial={"scholarship_session": session.pk if session else None, "status": Examination.Status.DRAFT})
        return render(request, "dashboard/simple_form.html", {"form": form, "page_title": "পরীক্ষা যোগ", "submit_label": "সংরক্ষণ"})

    def post(self, request):
        form = ExaminationForm(request.POST)
        if form.is_valid():
            exam = form.save()
            log_action(request=request, action="exam.create", instance=exam, changes={"status": exam.status})
            messages.success(request, "পরীক্ষা সংরক্ষণ হয়েছে। প্রকাশ আলাদাভাবে নিয়ন্ত্রণ করুন।")
            return redirect("examinations:list")
        return render(request, "dashboard/simple_form.html", {"form": form, "page_title": "পরীক্ষা যোগ", "submit_label": "সংরক্ষণ"})


class ExaminationUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        exam = get_object_or_404(Examination, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": ExaminationForm(instance=exam), "page_title": "পরীক্ষা সম্পাদনা", "submit_label": "হালনাগাদ"},
        )

    def post(self, request, pk):
        exam = get_object_or_404(Examination, pk=pk)
        form = ExaminationForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save()
            log_action(request=request, action="exam.update", instance=exam, changes={"status": exam.status})
            messages.success(request, "পরীক্ষা হালনাগাদ হয়েছে।")
            return redirect("examinations:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "পরীক্ষা সম্পাদনা", "submit_label": "হালনাগাদ"},
        )


class ExaminationPublishView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        exam = get_object_or_404(Examination, pk=pk)
        exam.status = Examination.Status.PUBLISHED if request.POST.get("publish") == "1" else Examination.Status.DRAFT
        exam.save(update_fields=["status", "updated_at"])
        log_action(request=request, action="exam.publish", instance=exam, changes={"status": exam.status})
        messages.success(request, "পরীক্ষার প্রকাশনা হালনাগাদ হয়েছে।")
        return redirect("examinations:list")
