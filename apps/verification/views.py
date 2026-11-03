from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.core.models import WebsiteSetting
from apps.students.models import Student
from apps.verification.services import set_verification_status
from apps.verification.statuses import VerificationStatus


class VerificationListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        status = request.GET.get("status") or VerificationStatus.PENDING
        if status not in VerificationStatus.values and status != "all":
            status = VerificationStatus.PENDING
        queryset = Student.objects.alive().select_related("institute", "academic_class", "category", "scholarship_session")
        if status != "all":
            queryset = queryset.filter(verification_status=status)
        paginator = Paginator(queryset.order_by("-created_at"), WebsiteSetting.load().students_per_page)
        page = paginator.get_page(request.GET.get("page") or 1)
        return render(
            request,
            "verification/list.html",
            {
                "page_title": "আবেদন যাচাই",
                "page_obj": page,
                "students": page.object_list,
                "statuses": VerificationStatus.choices,
                "current_status": status,
            },
        )


class VerificationReviewView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(
            Student.objects.alive().select_related("institute", "academic_class", "category", "scholarship_session"),
            pk=pk,
        )
        return render(
            request,
            "verification/review.html",
            {
                "student": student,
                "history": student.verification_history.select_related("verified_by"),
                "statuses": VerificationStatus.choices,
                "page_title": "যাচাই",
            },
        )

    def post(self, request, pk):
        student = get_object_or_404(Student.objects.alive(), pk=pk)
        try:
            set_verification_status(
                student=student,
                status=request.POST.get("status", ""),
                remarks=request.POST.get("remarks", ""),
                actor=request.user,
                request=request,
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "যাচাইয়ের অবস্থা সংরক্ষণ হয়েছে।")
        return redirect("verification:review", pk=student.pk)


class VerificationPrintView(SuperAdminRequiredMixin, View):
    def get(self, request):
        status = request.GET.get("status") or "all"
        queryset = Student.objects.alive().select_related("institute", "academic_class", "category")
        if status in VerificationStatus.values:
            queryset = queryset.filter(verification_status=status)
        return render(
            request,
            "verification/print.html",
            {"students": queryset.order_by("academic_class__display_order", "student_id"), "page_title": "যাচাই তালিকা"},
        )
