from django.shortcuts import render
from django.views import View

from apps.accounts.mixins import StaffRequiredMixin
from apps.audit.models import AuditLog
from apps.core.stats import dashboard_stats
from apps.sessions.selectors import get_active_session
from apps.students.models import Student


class DashboardView(StaffRequiredMixin, View):
    def get(self, request):
        session = get_active_session()
        recent = Student.objects.alive().select_related("institute", "academic_class")
        if session is not None:
            recent = recent.filter(scholarship_session=session)
        context = {
            "page_title": "ড্যাশবোর্ড",
            "stats": dashboard_stats(session),
            "recent_students": recent[:6],
            "recent_logs": AuditLog.objects.select_related("user")[:8] if request.user.is_super_admin else [],
        }
        return render(request, "dashboard/home.html", context)
