from django.urls import path

from apps.core.public_views import (
    AboutView,
    AnnouncementDismissView,
    AnnouncementSessionView,
    AnnouncementView,
    BrandAssetView,
    ContactView,
    HomeView,
    NoticeDetailView,
    NoticeListView,
    ProcessView,
    PublicNoticeAttachmentView,
    SchedulePageView,
    WinnerListView,
    WinnerPhotoView,
    robots_txt,
)

app_name = "public"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("application-process/", ProcessView.as_view(), name="process"),
    path("schedule/", SchedulePageView.as_view(), name="schedule"),
    path("notices/", NoticeListView.as_view(), name="notices"),
    path("notices/<str:slug>/", NoticeDetailView.as_view(), name="notice_detail"),
    path("notices/<str:slug>/attachment/", PublicNoticeAttachmentView.as_view(), name="notice_attachment"),
    path("announcement/", AnnouncementView.as_view(), name="announcement"),
    path("announcement/dismiss/", AnnouncementDismissView.as_view(), name="announcement_dismiss"),
    path("announcement/<slug:code>/", AnnouncementSessionView.as_view(), name="announcement_session"),
    path("winners/", WinnerListView.as_view(), name="winners"),
    path("winners/photo/<int:pk>/", WinnerPhotoView.as_view(), name="winner_photo"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("brand-assets/<slug:kind>/", BrandAssetView.as_view(), name="brand_asset"),
    path("robots.txt", robots_txt, name="robots"),
]
