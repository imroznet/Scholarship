from django.shortcuts import render
from django.views import View

from apps.accounts.mixins import StaffRequiredMixin, SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.reports.exporters import csv_response, student_rows, winner_rows, xlsx_response
from apps.results.models import Winner
from apps.students.queries import filtered_students


class ReportIndexView(StaffRequiredMixin, View):
    def get(self, request):
        return render(request, "reports/index.html", {"page_title": "রিপোর্ট ও এক্সপোর্ট", "filters": request.GET})


def _student_export(request, kind):
    queryset = filtered_students(request.GET, request.user)
    headers, rows = student_rows(queryset, request.user)
    log_action(
        request=request,
        action="export.students",
        target_model="students.Student",
        target_repr=kind,
        changes={"rows": len(rows), "filters": request.GET.dict()},
    )
    if kind == "csv":
        return csv_response("students.csv", headers, rows)
    return xlsx_response("students.xlsx", headers, rows)


class StudentCSVView(StaffRequiredMixin, View):
    def get(self, request):
        return _student_export(request, "csv")


class StudentXLSXView(StaffRequiredMixin, View):
    def get(self, request):
        return _student_export(request, "xlsx")


def _winner_queryset():
    return Winner.objects.select_related(
        "student",
        "student__institute",
        "student__academic_class",
        "award_type",
    )


class WinnerCSVView(SuperAdminRequiredMixin, View):
    def get(self, request):
        headers, rows = winner_rows(_winner_queryset())
        log_action(request=request, action="export.winners", target_model="results.Winner", target_repr="csv", changes={"rows": len(rows)})
        return csv_response("winners.csv", headers, rows)


class WinnerXLSXView(SuperAdminRequiredMixin, View):
    def get(self, request):
        headers, rows = winner_rows(_winner_queryset())
        log_action(request=request, action="export.winners", target_model="results.Winner", target_repr="xlsx", changes={"rows": len(rows)})
        return xlsx_response("winners.xlsx", headers, rows)


class StudentPrintListView(StaffRequiredMixin, View):
    def get(self, request):
        students = filtered_students(request.GET, request.user)[:1000]
        return render(
            request,
            "reports/print_students.html",
            {
                "students": students,
                "sensitive": request.user.is_super_admin,
                "page_title": "শিক্ষার্থী তালিকা",
            },
        )
