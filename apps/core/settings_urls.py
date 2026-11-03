from django.urls import path

from apps.core.views import SettingsView

app_name = "settings"

urlpatterns = [
    path("", SettingsView.as_view(), name="manage"),
]
