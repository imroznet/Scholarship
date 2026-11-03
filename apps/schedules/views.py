from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.schedules.forms import ScheduleForm
from apps.schedules.models import Schedule
from apps.schedules.services import activate_stage, deactivate_stage
from apps.sessions.models import ScholarshipSession
from apps.sessions.selectors import get_active_session


class ScheduleListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        raw = request.GET.get("session")
        if raw and str(raw).isdigit():
            session = get_object_or_404(ScholarshipSession, pk=raw)
        else:
            session = get_active_session() or ScholarshipSession.objects.order_by("-start_date").first()
        schedules = session.schedules.all() if session else []
        return render(
            request,
            "schedules/list.html",
            {
                "page_title": "সময়সূচি ব্যবস্থাপনা",
                "session": session,
                "sessions": ScholarshipSession.objects.order_by("-start_date"),
                "schedules": schedules,
            },
        )


class ScheduleUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": ScheduleForm(instance=schedule), "page_title": "সময়সূচি সম্পাদনা", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk)
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save(commit=False)
            if schedule.show_countdown and not schedule.countdown_target and schedule.end_at:
                schedule.countdown_target = schedule.end_at
            schedule.save()
            log_action(request=request, action="schedule.update", instance=schedule)
            messages.success(request, "সময়সূচি সংরক্ষণ হয়েছে। পর্যায় নিজে থেকে পরিবর্তন হয় না।")
            return redirect(f"/dashboard/schedules/?session={schedule.scholarship_session_id}")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "সময়সূচি সম্পাদনা", "submit_label": "সংরক্ষণ"},
        )


class ScheduleActivateView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk)
        try:
            activate_stage(schedule)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            log_action(request=request, action="schedule.activate", instance=schedule)
            messages.success(request, "পর্যায় সক্রিয় করা হয়েছে।")
        return redirect(f"/dashboard/schedules/?session={schedule.scholarship_session_id}")


class ScheduleDeactivateView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk)
        deactivate_stage(schedule)
        log_action(request=request, action="schedule.deactivate", instance=schedule)
        messages.success(request, "পর্যায় নিষ্ক্রিয় করা হয়েছে।")
        return redirect(f"/dashboard/schedules/?session={schedule.scholarship_session_id}")
