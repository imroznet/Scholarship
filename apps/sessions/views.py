from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.sessions.forms import SessionForm
from apps.sessions.models import ScholarshipSession
from apps.sessions.services import set_active_session


class SessionListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        sessions = ScholarshipSession.objects.all()
        return render(request, "sessions/list.html", {"sessions": sessions, "page_title": "স্কলারশিপ সেশন"})


class SessionCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": SessionForm(), "page_title": "সেশন যোগ", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request):
        form = SessionForm(request.POST)
        if form.is_valid():
            wants_active = form.cleaned_data["is_active"]
            with transaction.atomic():
                session = form.save(commit=False)
                session.is_active = False
                session.save()
                if wants_active:
                    set_active_session(session)
                session.branding.save()
            log_action(request=request, action="session.create", instance=session, changes={"active": wants_active})
            messages.success(request, "স্কলারশিপ সেশন তৈরি হয়েছে।")
            return redirect("sessions:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "সেশন যোগ", "submit_label": "সংরক্ষণ"},
        )


class SessionUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        session = get_object_or_404(ScholarshipSession, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": SessionForm(instance=session), "page_title": "সেশন সম্পাদনা", "submit_label": "হালনাগাদ"},
        )

    def post(self, request, pk):
        session = get_object_or_404(ScholarshipSession, pk=pk)
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            wants_active = form.cleaned_data["is_active"]
            with transaction.atomic():
                session = form.save(commit=False)
                session.is_active = False
                session.save()
                if wants_active:
                    set_active_session(session)
                session.branding.save()
            log_action(request=request, action="session.update", instance=session, changes={"active": wants_active})
            messages.success(request, "সেশন হালনাগাদ হয়েছে।")
            return redirect("sessions:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "সেশন সম্পাদনা", "submit_label": "হালনাগাদ"},
        )
