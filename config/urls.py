from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.public_urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.core.dashboard_urls")),
    path("dashboard/branding/", include("apps.branding.urls")),
    path("dashboard/sessions/", include("apps.sessions.urls")),
    path("dashboard/students/", include("apps.students.urls")),
    path("dashboard/institutes/", include("apps.institutes.urls")),
    path("dashboard/academics/", include("apps.academics.urls")),
    path("dashboard/verification/", include("apps.verification.urls")),
    path("dashboard/schedules/", include("apps.schedules.urls")),
    path("dashboard/examinations/", include("apps.examinations.urls")),
    path("dashboard/results/", include("apps.results.urls")),
    path("dashboard/winners/", include("apps.results.winner_urls")),
    path("dashboard/certificates/", include("apps.certificates.urls")),
    path("dashboard/notices/", include("apps.notices.urls")),
    path("dashboard/reports/", include("apps.reports.urls")),
    path("dashboard/users/", include("apps.accounts.user_urls")),
    path("dashboard/audit/", include("apps.audit.urls")),
    path("dashboard/settings/", include("apps.core.settings_urls")),
    path("django-admin/", admin.site.urls),
]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
