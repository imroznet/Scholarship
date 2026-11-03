from decimal import InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.core.models import WebsiteSetting
from apps.examinations.models import Examination
from apps.results.forms import AwardTypeForm, WinnerForm
from apps.results.models import AwardType, ExamResult, Winner
from apps.results.services import create_winner, save_result, set_winner_publication
from apps.students.models import Student


class ResultHomeView(SuperAdminRequiredMixin, View):
    def get(self, request):
        exams = Examination.objects.select_related("scholarship_session", "academic_class")
        return render(request, "results/home.html", {"exams": exams, "page_title": "ফলাফল ব্যবস্থাপনা"})


class ResultEntryView(SuperAdminRequiredMixin, View):
    def _exam(self, exam_id):
        return get_object_or_404(
            Examination.objects.select_related("academic_class", "scholarship_session"),
            pk=exam_id,
        )

    def _page(self, request, exam):
        students = Student.objects.alive().filter(
            scholarship_session=exam.scholarship_session,
            academic_class=exam.academic_class,
            is_active=True,
        ).select_related("institute").order_by("student_id")
        paginator = Paginator(students, WebsiteSetting.load().students_per_page)
        page = paginator.get_page(request.GET.get("page") or 1)
        existing = {
            result.student_id: result
            for result in ExamResult.objects.filter(examination=exam, student_id__in=[student.pk for student in page])
        }
        for student in page:
            student.result_row = existing.get(student.pk)
        return page

    def get(self, request, exam_id):
        exam = self._exam(exam_id)
        return render(
            request,
            "results/entry.html",
            {"exam": exam, "page_obj": self._page(request, exam), "page_title": "ফলাফল এন্ট্রি", "statuses": ExamResult.Status.choices},
        )

    def post(self, request, exam_id):
        exam = self._exam(exam_id)
        raw_ids = [int(pk) for pk in request.POST.getlist("student_ids") if str(pk).isdigit()]
        allowed = {
            student.pk: student
            for student in Student.objects.alive().filter(
                pk__in=raw_ids,
                scholarship_session=exam.scholarship_session,
                academic_class=exam.academic_class,
            )
        }
        try:
            with transaction.atomic():
                for pk, student in allowed.items():
                    raw_marks = (request.POST.get(f"marks-{pk}") or "").strip()
                    if raw_marks == "":
                        continue
                    status = request.POST.get(f"status-{pk}") or ExamResult.Status.DRAFT
                    if status not in ExamResult.Status.values:
                        raise ValidationError("অবৈধ ফলাফল অবস্থা।")
                    position_raw = (request.POST.get(f"position-{pk}") or "").strip()
                    position = int(position_raw) if position_raw.isdigit() else None
                    save_result(
                        student=student,
                        examination=exam,
                        obtained_marks=raw_marks,
                        remarks=request.POST.get(f"remarks-{pk}", ""),
                        position=position,
                        status=status,
                        actor=request.user,
                        request=request,
                    )
        except (ValidationError, InvalidOperation, ValueError) as exc:
            message = " ".join(getattr(exc, "messages", []) or [str(exc)])
            messages.error(request, message or "ফলাফল সংরক্ষণ করা যায়নি।")
        else:
            messages.success(request, "ফলাফল সংরক্ষণ হয়েছে। বিজয়ী স্বয়ংক্রিয়ভাবে নির্বাচিত হয়নি।")
        return redirect(f"/dashboard/results/{exam.pk}/?page={request.POST.get('page') or 1}")


class WinnerListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        winners = Winner.objects.select_related(
            "student", "student__institute", "student__academic_class", "award_type", "scholarship_session", "certificate"
        )
        return render(
            request,
            "results/winners.html",
            {
                "winners": winners,
                "form": WinnerForm(),
                "award_form": AwardTypeForm(),
                "awards": AwardType.objects.all(),
                "page_title": "বিজয়ী ব্যবস্থাপনা",
            },
        )

    def post(self, request):
        if request.POST.get("form") == "award":
            form = AwardTypeForm(request.POST)
            if form.is_valid():
                award = form.save()
                log_action(request=request, action="award.create", instance=award)
                messages.success(request, "পুরস্কারের ধরন সংরক্ষণ হয়েছে।")
            else:
                messages.error(request, "পুরস্কারের তথ্য সঠিক নয়।")
            return redirect("winners:list")
        form = WinnerForm(request.POST)
        if form.is_valid():
            result = None
            result_id = form.cleaned_data.get("result_reference")
            if result_id:
                result = ExamResult.objects.filter(pk=result_id, student=form.cleaned_data["student"]).first()
            try:
                create_winner(
                    student=form.cleaned_data["student"],
                    award_type=form.cleaned_data["award_type"],
                    position=form.cleaned_data.get("position"),
                    amount=form.cleaned_data.get("scholarship_amount"),
                    result=result,
                    actor=request.user,
                    request=request,
                )
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(request, "বিজয়ী নির্বাচন সংরক্ষণ হয়েছে। এখনো প্রকাশিত হয়নি।")
        else:
            messages.error(request, "বিজয়ীর তথ্য সঠিক নয়।")
        return redirect("winners:list")


class WinnerPublishView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        winner = get_object_or_404(Winner.objects.select_related("student"), pk=pk)
        publish = request.POST.get("publish") == "1"
        try:
            set_winner_publication(winner=winner, publish=publish, actor=request.user, request=request)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "প্রকাশনা হালনাগাদ হয়েছে।" if publish else "প্রকাশনা প্রত্যাহার হয়েছে।")
        return redirect("winners:list")


class WinnerPrintView(SuperAdminRequiredMixin, View):
    def get(self, request):
        winners = Winner.objects.filter(is_published=True).select_related(
            "student", "student__institute", "student__academic_class", "student__category", "award_type", "scholarship_session"
        )
        return render(request, "results/print_winners.html", {"winners": winners, "page_title": "বিজয়ী তালিকা"})
