from django.urls import path

from apps.examinations.views import (
    ExaminationCreateView,
    ExaminationListView,
    ExaminationPublishView,
    ExaminationUpdateView,
)

app_name = "examinations"

urlpatterns = [
    path("", ExaminationListView.as_view(), name="list"),
    path("new/", ExaminationCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", ExaminationUpdateView.as_view(), name="edit"),
    path("<int:pk>/publish/", ExaminationPublishView.as_view(), name="publish"),
]
