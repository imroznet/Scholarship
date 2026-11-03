from django.urls import path

from apps.results.views import WinnerListView, WinnerPrintView, WinnerPublishView

app_name = "winners"

urlpatterns = [
    path("", WinnerListView.as_view(), name="list"),
    path("print/", WinnerPrintView.as_view(), name="print"),
    path("<int:pk>/publish/", WinnerPublishView.as_view(), name="publish"),
]
