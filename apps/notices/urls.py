from django.urls import path

from apps.notices.views import (
    NoticeArchiveView,
    NoticeAttachmentView,
    NoticeCreateView,
    NoticeListView,
    NoticeUpdateView,
)

app_name = "notices"

urlpatterns = [
    path("", NoticeListView.as_view(), name="list"),
    path("new/", NoticeCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", NoticeUpdateView.as_view(), name="edit"),
    path("<int:pk>/archive/", NoticeArchiveView.as_view(), name="archive"),
    path("<int:pk>/attachment/", NoticeAttachmentView.as_view(), name="attachment"),
]
