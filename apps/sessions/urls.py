from django.urls import path

from apps.sessions.views import SessionCreateView, SessionListView, SessionUpdateView

app_name = "sessions"

urlpatterns = [
    path("", SessionListView.as_view(), name="list"),
    path("new/", SessionCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", SessionUpdateView.as_view(), name="edit"),
]
