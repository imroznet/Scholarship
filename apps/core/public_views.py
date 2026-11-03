from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.core.http import guarded_file_response
from apps.examinations.models import Examination
from apps.notices.models import Notice, public_notices
from apps.results.announcements import (
    DISMISS_COOKIE,
    dismissal_token,
    landing_announcement,
    published_winner_queryset,
    visitor_has_dismissed,
)
from apps.results.models import Winner, WinnerAnnouncement
from apps.schedules.models import Schedule
from apps.sessions.models import ScholarshipSession
from apps.sessions.selectors import get_active_session

PUBLIC_ASSETS = {
    "logo": "logo",
    "sponsor-logo": "sponsor_logo",
    "favicon": "favicon",
    "secondary-logo": "secondary_logo",
}


def published_winners(session):
    return published_winner_queryset(session)


class HomeView(TemplateView):
    template_name = "public/home.html"

    def get(self, request, *args, **kwargs):
        announcement = landing_announcement(get_active_session())
        if (
            announcement is not None
            and request.GET.get("home") != "1"
            and not visitor_has_dismissed(request, announcement)
        ):
            return redirect("public:announcement")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        context["schedule"] = None
        context["notices"] = []
        context["winners"] = []
        context["exams"] = []
        if session is None:
            return context
        context["schedule"] = Schedule.objects.filter(scholarship_session=session, is_active=True).first()
        context["notices"] = public_notices(session)[:5]
        context["winners"] = published_winners(session)[:8]
        context["exams"] = (
            Examination.objects.filter(scholarship_session=session, status=Examination.Status.PUBLISHED)
            .select_related("academic_class")
            .order_by("exam_date", "start_time")
        )
        return context


class AboutView(TemplateView):
    template_name = "public/about.html"


class ProcessView(TemplateView):
    template_name = "public/application_process.html"


class SchedulePageView(TemplateView):
    template_name = "public/schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        context["schedules"] = []
        context["active_stage"] = None
        if session is not None:
            context["schedules"] = session.schedules.all()
            context["active_stage"] = context["schedules"].filter(is_active=True).first()
        return context


class NoticeListView(TemplateView):
    template_name = "public/notices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        context["notices"] = public_notices(session) if session else Notice.objects.none()
        return context


class NoticeDetailView(TemplateView):
    template_name = "public/notice_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        if session is None:
            raise Http404
        notice = get_object_or_404(public_notices(session), slug=self.kwargs["slug"])
        context["notice"] = notice
        return context


class AnnouncementView(TemplateView):
    template_name = "public/announcement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        announcement = landing_announcement(session)
        context["announcement"] = announcement
        context["winners"] = published_winners(session) if announcement else Winner.objects.none()
        context["announcement_token"] = dismissal_token(announcement) if announcement else ""
        context["page_branding"] = getattr(session, "branding", None) if session else None
        return context


class AnnouncementSessionView(TemplateView):
    template_name = "public/announcement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_object_or_404(ScholarshipSession, code=self.kwargs["code"])
        announcement = (
            WinnerAnnouncement.objects.filter(
                scholarship_session=session,
                is_published=True,
            )
            .select_related("scholarship_session")
            .first()
        )
        if announcement is None:
            raise Http404
        context["announcement"] = announcement
        context["winners"] = published_winners(session)
        context["announcement_token"] = ""
        context["page_branding"] = getattr(session, "branding", None)
        context["historical"] = True
        if context["page_branding"] is not None:
            context["branding"] = context["page_branding"]
        return context


class AnnouncementDismissView(View):
    def get(self, request):
        announcement = landing_announcement(get_active_session())
        response = redirect("public:home")
        if announcement is not None:
            response.set_cookie(
                DISMISS_COOKIE,
                dismissal_token(announcement),
                max_age=60 * 60 * 24 * 365,
                samesite="Lax",
                secure=request.is_secure(),
                httponly=False,
                path="/",
            )
        return response


class WinnerListView(TemplateView):
    template_name = "public/winners.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = get_active_session()
        context["winners"] = published_winners(session) if session else Winner.objects.none()
        return context


class ContactView(TemplateView):
    template_name = "public/contact.html"


class BrandAssetView(View):
    def get(self, request, kind):
        field_name = PUBLIC_ASSETS.get(kind)
        session = get_active_session()
        if not field_name or session is None or not hasattr(session, "branding"):
            raise Http404
        return guarded_file_response(
            getattr(session.branding, field_name),
            cache_control="public, max-age=86400",
        )


class WinnerPhotoView(View):
    def get(self, request, pk):
        winner = get_object_or_404(
            Winner.objects.select_related("student"),
            pk=pk,
            is_published=True,
            student__deleted_at__isnull=True,
            student__is_active=True,
        )
        return guarded_file_response(winner.student.photo, cache_control="public, max-age=3600")


class PublicNoticeAttachmentView(View):
    def get(self, request, slug):
        session = get_active_session()
        if session is None:
            raise Http404
        notice = get_object_or_404(public_notices(session), slug=slug)
        return guarded_file_response(
            notice.attachment,
            download_name=notice.attachment_name or "attachment",
            cache_control="public, max-age=3600",
        )


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Disallow: /django-admin/",
        "Disallow: /media/",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
