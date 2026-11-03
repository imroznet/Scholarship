from django.urls import path

from apps.reports.views import (
    ReportIndexView,
    StudentCSVView,
    StudentPrintListView,
    StudentXLSXView,
    WinnerCSVView,
    WinnerXLSXView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportIndexView.as_view(), name="index"),
    path("students.csv", StudentCSVView.as_view(), name="students_csv"),
    path("students.xlsx", StudentXLSXView.as_view(), name="students_xlsx"),
    path("winners.csv", WinnerCSVView.as_view(), name="winners_csv"),
    path("winners.xlsx", WinnerXLSXView.as_view(), name="winners_xlsx"),
    path("students/print/", StudentPrintListView.as_view(), name="print_students"),
]
