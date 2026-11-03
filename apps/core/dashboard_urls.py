from django.urls import path

from apps.core.dashboard_views import DashboardView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="home"),
]
