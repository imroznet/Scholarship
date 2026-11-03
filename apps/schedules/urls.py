from django.urls import path

from apps.schedules.views import (
    ScheduleActivateView,
    ScheduleDeactivateView,
    ScheduleListView,
    ScheduleUpdateView,
)

app_name = "schedules"

urlpatterns = [
    path("", ScheduleListView.as_view(), name="list"),
    path("<int:pk>/edit/", ScheduleUpdateView.as_view(), name="edit"),
    path("<int:pk>/activate/", ScheduleActivateView.as_view(), name="activate"),
    path("<int:pk>/deactivate/", ScheduleDeactivateView.as_view(), name="deactivate"),
]
