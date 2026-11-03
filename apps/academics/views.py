from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View

from apps.academics.forms import AcademicClassForm
from apps.academics.models import AcademicClass, ClassRegistrationSetting
from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.sessions.models import ScholarshipSession
from apps.sessions.selectors import get_active_session


class ClassListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        session = get_active_session()
        student_filter = Q(students__deleted_at__isnull=True)
        if session is not None:
            student_filter &= Q(students__scholarship_session=session)
        classes = AcademicClass.objects.annotate(student_count=Count("students", filter=student_filter))
        return render(request, "academics/classes.html", {"classes": classes, "page_title": "শ্রেণি ব্যবস্থাপনা"})


class ClassCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": AcademicClassForm(), "page_title": "শ্রেণি যোগ", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request):
        form = AcademicClassForm(request.POST)
        if form.is_valid():
            academic_class = form.save()
            log_action(request=request, action="class.create", instance=academic_class)
            messages.success(request, "শ্রেণি সংরক্ষণ হয়েছে।")
            return redirect("academics:classes")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "শ্রেণি যোগ", "submit_label": "সংরক্ষণ"},
        )


class ClassUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        academic_class = get_object_or_404(AcademicClass, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": AcademicClassForm(instance=academic_class), "page_title": "শ্রেণি সম্পাদনা", "submit_label": "হালনাগাদ"},
        )

    def post(self, request, pk):
        academic_class = get_object_or_404(AcademicClass, pk=pk)
        form = AcademicClassForm(request.POST, instance=academic_class)
        if form.is_valid():
            academic_class = form.save()
            log_action(request=request, action="class.update", instance=academic_class)
            messages.success(request, "শ্রেণি হালনাগাদ হয়েছে।")
            return redirect("academics:classes")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "শ্রেণি সম্পাদনা", "submit_label": "হালনাগাদ"},
        )


def _aware(value):
    if value and timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


class RegistrationControlView(SuperAdminRequiredMixin, View):
    def _session(self, request):
        session_id = request.GET.get("session") or request.POST.get("session")
        if session_id and str(session_id).isdigit():
            return get_object_or_404(ScholarshipSession, pk=session_id)
        return get_active_session() or ScholarshipSession.objects.order_by("-start_date").first()

    def get(self, request):
        session = self._session(request)
        rows = []
        if session is not None:
            rows = ClassRegistrationSetting.objects.filter(scholarship_session=session).select_related("academic_class")
        return render(
            request,
            "academics/registration.html",
            {
                "page_title": "নিবন্ধন নিয়ন্ত্রণ",
                "session": session,
                "sessions": ScholarshipSession.objects.order_by("-start_date"),
                "rows": rows,
            },
        )

    def post(self, request):
        session = self._session(request)
        if session is None:
            messages.error(request, "আগে একটি স্কলারশিপ সেশন তৈরি করুন।")
            return redirect("academics:registration")
        action = request.POST.get("action")
        selected = [pk for pk in request.POST.getlist("class_ids") if str(pk).isdigit()]
        rows = ClassRegistrationSetting.objects.filter(scholarship_session=session, academic_class_id__in=selected)
        if action in {"open", "close"}:
            rows.update(is_open=(action == "open"))
            log_action(
                request=request,
                action=f"registration.{action}",
                target_model="academics.ClassRegistrationSetting",
                target_repr=session.code,
                changes={"classes": selected},
            )
            messages.success(request, "নিবন্ধন অবস্থা হালনাগাদ হয়েছে।")
        elif action == "schedule":
            row = get_object_or_404(
                ClassRegistrationSetting,
                pk=request.POST.get("row_id"),
                scholarship_session=session,
            )
            opening = _aware(parse_datetime(request.POST.get("opening_at") or ""))
            closing = _aware(parse_datetime(request.POST.get("closing_at") or ""))
            if opening and closing and closing <= opening:
                messages.error(request, "বন্ধ হওয়ার সময় শুরুর পরে হতে হবে।")
            else:
                row.opening_at = opening
                row.closing_at = closing
                row.is_open = request.POST.get("is_open") == "1"
                row.save()
                log_action(request=request, action="registration.schedule", instance=row)
                messages.success(request, "নিবন্ধনের সময় সংরক্ষণ হয়েছে।")
        return redirect(f"{request.path}?session={session.pk}")
