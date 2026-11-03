from django.urls import path

from apps.results.views import ResultEntryView, ResultHomeView

app_name = "results"

urlpatterns = [
    path("", ResultHomeView.as_view(), name="home"),
    path("<int:exam_id>/", ResultEntryView.as_view(), name="entry"),
]
