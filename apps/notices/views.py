from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.mixins import StaffRequiredMixin, SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.core.http import guarded_file_response
from apps.core.models import WebsiteSetting
from apps.core.uploads import process_attachment
from apps.notices.forms import NoticeForm
from apps.notices.models import Notice
from apps.notices.services import unique_slug
from apps.sessions.selectors import get_active_session


class NoticeListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        notices = Notice.objects.select_related("scholarship_session", "created_by")
        return render(request, "notices/list.html", {"notices": notices, "page_title": "নোটিশ"})


class NoticeCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        session = get_active_session()
        form = NoticeForm(initial={"scholarship_session": getattr(session, "pk", None), "status": Notice.Status.DRAFT})
        return render(request, "notices/form.html", {"form": form, "page_title": "নোটিশ যোগ"})

    def post(self, request):
        form = NoticeForm(request.POST)
        attachment_error = None
        stored = None
        original_name = ""
        upload = request.FILES.get("attachment")
        if upload:
            try:
                stored, original_name = process_attachment(
                    upload,
                    max_bytes=min(WebsiteSetting.load().max_attachment_mb, 8) * 1024 * 1024,
                )
            except ValidationError as exc:
                attachment_error = exc
        if form.is_valid() and attachment_error is None:
            notice = form.save(commit=False)
            if not notice.slug:
                notice.slug = unique_slug(notice.title_bn, notice)
            else:
                notice.slug = unique_slug(notice.slug, notice)
            if notice.status == Notice.Status.PUBLISHED and not notice.published_at:
                notice.published_at = timezone.now()
            notice.created_by = request.user
            if stored is not None:
                notice.attachment.save(stored.name, stored, save=False)
                notice.attachment_name = original_name
            notice.save()
            log_action(request=request, action="notice.create", instance=notice, changes={"status": notice.status})
            messages.success(request, "নোটিশ সংরক্ষণ হয়েছে।")
            return redirect("notices:list")
        if attachment_error is not None:
            form.add_error(None, attachment_error)
        return render(request, "notices/form.html", {"form": form, "page_title": "নোটিশ যোগ"})


class NoticeUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        notice = get_object_or_404(Notice, pk=pk)
        return render(request, "notices/form.html", {"form": NoticeForm(instance=notice), "notice": notice, "page_title": "নোটিশ সম্পাদনা"})

    def post(self, request, pk):
        notice = get_object_or_404(Notice, pk=pk)
        form = NoticeForm(request.POST, instance=notice)
        attachment_error = None
        stored = None
        original_name = ""
        upload = request.FILES.get("attachment")
        if upload:
            try:
                stored, original_name = process_attachment(
                    upload,
                    max_bytes=min(WebsiteSetting.load().max_attachment_mb, 8) * 1024 * 1024,
                )
            except ValidationError as exc:
                attachment_error = exc
        if form.is_valid() and attachment_error is None:
            notice = form.save(commit=False)
            if not notice.slug:
                notice.slug = unique_slug(notice.title_bn, notice)
            if notice.status == Notice.Status.PUBLISHED and not notice.published_at:
                notice.published_at = timezone.now()
            if stored is not None:
                if notice.attachment:
                    notice.attachment.delete(save=False)
                notice.attachment.save(stored.name, stored, save=False)
                notice.attachment_name = original_name
            notice.save()
            log_action(request=request, action="notice.update", instance=notice, changes={"status": notice.status})
            messages.success(request, "নোটিশ হালনাগাদ হয়েছে।")
            return redirect("notices:list")
        if attachment_error is not None:
            form.add_error(None, attachment_error)
        return render(request, "notices/form.html", {"form": form, "notice": notice, "page_title": "নোটিশ সম্পাদনা"})


class NoticeArchiveView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        notice = get_object_or_404(Notice, pk=pk)
        if notice.status == Notice.Status.DRAFT and request.POST.get("hard") == "1":
            if notice.attachment:
                notice.attachment.delete(save=False)
            log_action(request=request, action="notice.delete", instance=notice)
            notice.delete()
            messages.success(request, "খসড়া নোটিশ মুছে ফেলা হয়েছে।")
        else:
            notice.status = Notice.Status.ARCHIVED
            notice.is_featured = False
            notice.save(update_fields=["status", "is_featured", "updated_at"])
            log_action(request=request, action="notice.archive", instance=notice)
            messages.success(request, "নোটিশ আর্কাইভ করা হয়েছে।")
        return redirect("notices:list")


class NoticeAttachmentView(StaffRequiredMixin, View):
    def get(self, request, pk):
        notice = get_object_or_404(Notice, pk=pk)
        return guarded_file_response(notice.attachment, download_name=notice.attachment_name or "attachment")
