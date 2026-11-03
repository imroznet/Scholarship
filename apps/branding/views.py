from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from django.core.exceptions import PermissionDenied

from apps.accounts.mixins import StaffRequiredMixin, SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.branding.forms import BrandingForm
from apps.branding.services import apply_brand_images, reset_branding
from apps.core.http import guarded_file_response
from apps.core.models import WebsiteSetting
from apps.sessions.models import ScholarshipSession
from apps.sessions.selectors import get_active_session
from apps.sessions.services import ensure_session_dependencies

ADMIN_ASSETS = {
    "logo": "logo",
    "logo-original": "logo_original",
    "sponsor-logo": "sponsor_logo",
    "sponsor-original": "sponsor_logo_original",
    "favicon": "favicon",
    "secondary-logo": "secondary_logo",
    "secondary-original": "secondary_logo_original",
    "signature": "signature_image",
    "seal": "seal_image",
}


class BrandingManageView(SuperAdminRequiredMixin, View):
    template_name = "branding/manage.html"

    def _session(self, request):
        raw = request.GET.get("session") or request.POST.get("session")
        if raw and str(raw).isdigit():
            session = get_object_or_404(ScholarshipSession, pk=raw)
        else:
            session = get_active_session() or ScholarshipSession.objects.order_by("-start_date").first()
        if session is None:
            return None
        ensure_session_dependencies(session)
        return session

    def get(self, request):
        session = self._session(request)
        form = BrandingForm(instance=session.branding) if session else None
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "session": session,
                "sessions": ScholarshipSession.objects.order_by("-start_date"),
                "page_title": "স্কলারশিপ পরিচিতি ও ব্র্যান্ডিং",
            },
        )

    def post(self, request):
        session = self._session(request)
        if session is None:
            messages.error(request, "আগে একটি স্কলারশিপ সেশন তৈরি করুন।")
            return redirect("sessions:list")
        if request.POST.get("reset") == "1":
            if request.POST.get("confirm_reset") != "1":
                messages.error(request, "রিসেট নিশ্চিত করতে ঘরে টিক দিন।")
                return redirect(f"{request.path}?session={session.pk}")
            reset_branding(session.branding)
            log_action(request=request, action="branding.reset", instance=session.branding)
            messages.success(request, "ব্র্যান্ডিং নির্ধারিত অবস্থায় ফিরিয়ে আনা হয়েছে।")
            return redirect(f"{request.path}?session={session.pk}")
        form = BrandingForm(request.POST, instance=session.branding)
        if form.is_valid():
            max_bytes = min(WebsiteSetting.load().max_logo_mb, 8) * 1024 * 1024
            clear_fields = [name for name in ("logo", "sponsor_logo", "favicon", "secondary_logo", "signature_image", "seal_image") if request.POST.get(f"clear_{name}")]
            try:
                with transaction.atomic():
                    branding = form.save()
                    apply_brand_images(branding, request.FILES, max_bytes=max_bytes, clear_fields=clear_fields)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                log_action(request=request, action="branding.update", instance=branding)
                messages.success(request, "ব্র্যান্ডিং সংরক্ষণ হয়েছে।")
                return redirect(f"{request.path}?session={session.pk}")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "session": session,
                "sessions": ScholarshipSession.objects.order_by("-start_date"),
                "page_title": "স্কলারশিপ পরিচিতি ও ব্র্যান্ডিং",
            },
        )


class BrandAssetAdminView(StaffRequiredMixin, View):
    def get(self, request, pk, kind):
        field_name = ADMIN_ASSETS.get(kind)
        if not field_name:
            raise Http404
        if kind not in {"logo", "sponsor-logo", "favicon", "secondary-logo"} and not request.user.is_super_admin:
            raise PermissionDenied
        session = get_object_or_404(ScholarshipSession.objects.select_related("branding"), pk=pk)
        return guarded_file_response(getattr(session.branding, field_name))
