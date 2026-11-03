from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.academics.models import AcademicClass, open_registration_settings
from apps.accounts.mixins import StaffRequiredMixin, SuperAdminRequiredMixin
from apps.core.models import WebsiteSetting
from apps.core.uploads import process_image
from apps.institutes.models import Category, Institute
from apps.sessions.models import ScholarshipSession
from apps.sessions.selectors import get_active_session
from apps.students.forms import StudentForm
from apps.students.models import Student
from apps.students.queries import filtered_students
from apps.students.services import (
    clear_stashed_image,
    find_duplicate_warnings,
    read_stashed_image,
    register_student,
    restore_student,
    soft_delete_student,
    stashed_image_path,
    stash_processed_image,
    update_student,
)
from apps.verification.statuses import VerificationStatus


def _photo_limit():
    return min(WebsiteSetting.load().max_photo_mb, 8) * 1024 * 1024


class StudentListView(StaffRequiredMixin, View):
    def get(self, request):
        queryset = filtered_students(request.GET, request.user)
        paginator = Paginator(queryset, WebsiteSetting.load().students_per_page)
        page = paginator.get_page(request.GET.get("page") or 1)
        context = {
            "page_title": "শিক্ষার্থী ব্যবস্থাপনা",
            "page_obj": page,
            "students": page.object_list,
            "institutes": Institute.objects.filter(is_active=True).order_by("name_bn"),
            "classes": AcademicClass.objects.filter(is_active=True).order_by("display_order", "name_bn"),
            "categories": Category.objects.filter(is_active=True).order_by("name_bn"),
            "sessions": ScholarshipSession.objects.order_by("-start_date"),
            "statuses": VerificationStatus.choices,
            "filters": request.GET,
        }
        template = "students/partials/table.html" if request.headers.get("HX-Request") else "students/list.html"
        return render(request, template, context)


class StudentCreateView(StaffRequiredMixin, View):
    template_name = "students/form.html"

    def _institutes(self):
        return Institute.objects.filter(is_active=True).select_related("category").order_by("name_bn")

    def _classes(self):
        session = get_active_session()
        if session is None:
            return AcademicClass.objects.none()
        open_ids = open_registration_settings(session).values("academic_class_id")
        return AcademicClass.objects.filter(pk__in=open_ids).order_by("display_order", "name_bn")

    def _context(self, request, form, warnings=None):
        return {
            "form": form,
            "page_title": "শিক্ষার্থী নিবন্ধন",
            "institutes": self._institutes(),
            "warnings": warnings or [],
            "photo_saved": bool(stashed_image_path(request)),
            "is_edit": False,
            "active_session": get_active_session(),
        }

    def get(self, request):
        form = StudentForm(institutes=self._institutes(), classes=self._classes())
        return render(request, self.template_name, self._context(request, form))

    def post(self, request):
        form = StudentForm(request.POST, institutes=self._institutes(), classes=self._classes())
        photo_error = None
        upload = request.FILES.get("photo")
        if upload:
            try:
                display, _original = process_image(upload, max_bytes=_photo_limit(), max_px=800)
                stash_processed_image(request, display)
            except ValidationError as exc:
                photo_error = exc
        if form.is_valid() and photo_error is None:
            path = stashed_image_path(request)
            if not path:
                form.add_error("photo", "শিক্ষার্থীর ছবি আবশ্যক।")
            else:
                cleaned = form.cleaned_data
                warnings = find_duplicate_warnings(
                    name_bn=cleaned["name_bn"],
                    name_en=cleaned["name_en"],
                    date_of_birth=cleaned["date_of_birth"],
                    mobile=cleaned["mobile"],
                    father_mobile=cleaned.get("father_mobile") or "",
                    institute=cleaned["institute"],
                )
                if warnings and not request.POST.get("confirm_duplicates"):
                    return render(request, self.template_name, self._context(request, form, warnings))
                try:
                    student = register_student(
                        actor=request.user,
                        photo=read_stashed_image(path),
                        cleaned=cleaned,
                        request=request,
                    )
                except ValidationError as exc:
                    form.add_error(None, exc)
                else:
                    clear_stashed_image(request)
                    messages.success(request, "সফলভাবে শিক্ষার্থী নিবন্ধন সম্পন্ন হয়েছে।")
                    return redirect("students:registered", pk=student.pk)
        if photo_error is not None:
            form.add_error("photo", photo_error)
        return render(request, self.template_name, self._context(request, form))


class StudentRegisteredView(StaffRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(
            Student.objects.alive().select_related("institute", "academic_class", "category"),
            pk=pk,
        )
        return render(request, "students/registered.html", {"student": student, "page_title": "নিবন্ধন সম্পন্ন"})


class StudentDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        queryset = Student.objects.select_related(
            "institute", "category", "academic_class", "scholarship_session", "registered_by"
        )
        if not request.user.is_super_admin:
            queryset = queryset.alive().filter(is_active=True)
        student = get_object_or_404(queryset, pk=pk)
        history = student.verification_history.select_related("verified_by")
        return render(
            request,
            "students/detail.html",
            {"student": student, "history": history, "page_title": student.student_id},
        )


class StudentUpdateView(StaffRequiredMixin, View):
    template_name = "students/form.html"

    def _student(self, request, pk):
        queryset = Student.objects.alive().select_related("institute", "academic_class", "scholarship_session")
        if not request.user.is_super_admin:
            queryset = queryset.filter(is_active=True)
        return get_object_or_404(queryset, pk=pk)

    def _institutes(self, student):
        return (
            Institute.objects.filter(Q(is_active=True) | Q(pk=student.institute_id))
            .select_related("category")
            .order_by("name_bn")
        )

    def _classes(self, request, student):
        if request.user.is_super_admin:
            return AcademicClass.objects.filter(is_active=True).order_by("display_order", "name_bn")
        open_ids = open_registration_settings(student.scholarship_session).values("academic_class_id")
        return AcademicClass.objects.filter(Q(pk__in=open_ids) | Q(pk=student.academic_class_id)).order_by(
            "display_order", "name_bn"
        )

    def _initial(self, student):
        return {
            "name_bn": student.name_bn,
            "name_en": student.name_en,
            "date_of_birth": student.date_of_birth,
            "mobile": student.mobile,
            "father_name": student.father_name,
            "father_mobile": student.father_mobile,
            "mother_name": student.mother_name,
            "mother_mobile": student.mother_mobile,
            "village": student.village,
            "post_office": student.post_office,
            "upazila": student.upazila,
            "district": student.district,
            "institute": student.institute_id,
            "academic_class": student.academic_class_id,
            "is_active": student.is_active,
        }

    def _context(self, request, student, form, warnings=None):
        return {
            "form": form,
            "student": student,
            "page_title": "শিক্ষার্থী সম্পাদনা",
            "institutes": self._institutes(student),
            "warnings": warnings or [],
            "photo_saved": bool(stashed_image_path(request, f"edit-photo-{student.pk}")),
            "is_edit": True,
            "active_session": student.scholarship_session,
        }

    def get(self, request, pk):
        student = self._student(request, pk)
        form = StudentForm(
            initial=self._initial(student),
            institutes=self._institutes(student),
            classes=self._classes(request, student),
            include_active=request.user.is_super_admin,
        )
        return render(request, self.template_name, self._context(request, student, form))

    def post(self, request, pk):
        student = self._student(request, pk)
        form = StudentForm(
            request.POST,
            institutes=self._institutes(student),
            classes=self._classes(request, student),
            include_active=request.user.is_super_admin,
        )
        photo_key = f"edit-photo-{student.pk}"
        photo_error = None
        upload = request.FILES.get("photo")
        if upload:
            try:
                display, _original = process_image(upload, max_bytes=_photo_limit(), max_px=800)
                stash_processed_image(request, display, key=photo_key)
            except ValidationError as exc:
                photo_error = exc
        if form.is_valid() and photo_error is None:
            cleaned = form.cleaned_data
            warnings = find_duplicate_warnings(
                name_bn=cleaned["name_bn"],
                name_en=cleaned["name_en"],
                date_of_birth=cleaned["date_of_birth"],
                mobile=cleaned["mobile"],
                father_mobile=cleaned.get("father_mobile") or "",
                institute=cleaned["institute"],
                exclude_pk=student.pk,
            )
            if warnings and not request.POST.get("confirm_duplicates"):
                return render(request, self.template_name, self._context(request, student, form, warnings))
            path = stashed_image_path(request, photo_key)
            photo = read_stashed_image(path) if path else None
            try:
                update_student(student=student, actor=request.user, cleaned=cleaned, photo=photo, request=request)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                clear_stashed_image(request, photo_key)
                messages.success(request, "শিক্ষার্থীর তথ্য হালনাগাদ হয়েছে।")
                return redirect("students:detail", pk=student.pk)
        if photo_error is not None:
            form.add_error("photo", photo_error)
        return render(request, self.template_name, self._context(request, student, form))


class StudentPhotoView(StaffRequiredMixin, View):
    def get(self, request, pk):
        from apps.core.http import guarded_file_response

        queryset = Student.objects.all()
        if not request.user.is_super_admin:
            queryset = queryset.alive()
        student = get_object_or_404(queryset, pk=pk)
        return guarded_file_response(student.photo)


class StudentPrintView(StaffRequiredMixin, View):
    def get(self, request, pk):
        queryset = Student.objects.alive().select_related(
            "institute", "category", "academic_class", "scholarship_session", "scholarship_session__branding"
        )
        student = get_object_or_404(queryset, pk=pk)
        return render(request, "students/print_profile.html", {"student": student, "page_title": "শিক্ষার্থী প্রোফাইল"})


class StudentDeleteView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student.objects.alive(), pk=pk)
        soft_delete_student(student=student, actor=request.user, request=request)
        messages.success(request, "শিক্ষার্থীর রেকর্ড সরিয়ে রাখা হয়েছে। আইডি আর ব্যবহার করা হবে না।")
        return redirect("students:list")


class StudentRestoreView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk, deleted_at__isnull=False)
        restore_student(student=student, actor=request.user, request=request)
        messages.success(request, "শিক্ষার্থীর রেকর্ড ফিরিয়ে আনা হয়েছে।")
        return redirect("students:detail", pk=student.pk)
