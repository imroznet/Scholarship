from django.urls import path

from apps.students.views import (
    StudentCreateView,
    StudentDeleteView,
    StudentDetailView,
    StudentListView,
    StudentPhotoView,
    StudentPrintView,
    StudentRegisteredView,
    StudentRestoreView,
    StudentUpdateView,
)

app_name = "students"

urlpatterns = [
    path("", StudentListView.as_view(), name="list"),
    path("new/", StudentCreateView.as_view(), name="create"),
    path("<int:pk>/", StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", StudentUpdateView.as_view(), name="edit"),
    path("<int:pk>/registered/", StudentRegisteredView.as_view(), name="registered"),
    path("<int:pk>/photo/", StudentPhotoView.as_view(), name="photo"),
    path("<int:pk>/print/", StudentPrintView.as_view(), name="print"),
    path("<int:pk>/delete/", StudentDeleteView.as_view(), name="delete"),
    path("<int:pk>/restore/", StudentRestoreView.as_view(), name="restore"),
]
