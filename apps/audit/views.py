from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.models import AuditLog


class AuditListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        logs = AuditLog.objects.select_related("user")
        action = (request.GET.get("action") or "").strip()
        if action:
            logs = logs.filter(action__icontains=action)
        user_id = request.GET.get("user")
        if user_id and str(user_id).isdigit():
            logs = logs.filter(user_id=user_id)
        paginator = Paginator(logs, 50)
        page = paginator.get_page(request.GET.get("page") or 1)
        return render(
            request,
            "audit/list.html",
            {"page_title": "কার্যক্রম লগ", "page_obj": page, "logs": page.object_list, "action": action},
        )
