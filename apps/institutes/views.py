from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.audit.services import log_action
from apps.institutes.forms import CategoryForm, InstituteForm
from apps.institutes.models import Category, Institute


class InstituteListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        query = (request.GET.get("q") or "").strip()
        institutes = Institute.objects.select_related("category").order_by("name_bn")
        if query:
            institutes = institutes.filter(
                Q(name_bn__icontains=query) | Q(name_en__icontains=query) | Q(institute_code__icontains=query)
            )
        return render(
            request,
            "institutes/list.html",
            {"institutes": institutes, "page_title": "শিক্ষা প্রতিষ্ঠান", "query": query},
        )


class InstituteCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": InstituteForm(), "page_title": "প্রতিষ্ঠান যোগ", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request):
        form = InstituteForm(request.POST)
        if form.is_valid():
            institute = form.save()
            log_action(request=request, action="institute.create", instance=institute)
            messages.success(request, "প্রতিষ্ঠান সংরক্ষণ হয়েছে।")
            return redirect("institutes:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "প্রতিষ্ঠান যোগ", "submit_label": "সংরক্ষণ"},
        )


class InstituteUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        institute = get_object_or_404(Institute, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {
                "form": InstituteForm(instance=institute),
                "page_title": "প্রতিষ্ঠান সম্পাদনা",
                "submit_label": "হালনাগাদ",
                "note": "বিভাগ বদলালে আগের শিক্ষার্থীদের সংরক্ষিত বিভাগ পরিবর্তন হবে না।",
            },
        )

    def post(self, request, pk):
        institute = get_object_or_404(Institute, pk=pk)
        form = InstituteForm(request.POST, instance=institute)
        if form.is_valid():
            institute = form.save()
            log_action(request=request, action="institute.update", instance=institute)
            messages.success(request, "প্রতিষ্ঠান হালনাগাদ হয়েছে।")
            return redirect("institutes:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "প্রতিষ্ঠান সম্পাদনা", "submit_label": "হালনাগাদ"},
        )


class InstituteDeactivateView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        institute = get_object_or_404(Institute, pk=pk)
        institute.is_active = False
        institute.save(update_fields=["is_active", "updated_at"])
        log_action(request=request, action="institute.deactivate", instance=institute)
        messages.success(request, "প্রতিষ্ঠান নিষ্ক্রিয় করা হয়েছে।")
        return redirect("institutes:list")


class CategoryListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "institutes/categories.html",
            {"categories": Category.objects.all(), "page_title": "বিভাগ ব্যবস্থাপনা"},
        )


class CategoryCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": CategoryForm(), "page_title": "বিভাগ যোগ", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            log_action(request=request, action="category.create", instance=category)
            messages.success(request, "বিভাগ সংরক্ষণ হয়েছে।")
            return redirect("institutes:categories")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "বিভাগ যোগ", "submit_label": "সংরক্ষণ"},
        )


class CategoryUpdateView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": CategoryForm(instance=category), "page_title": "বিভাগ সম্পাদনা", "submit_label": "হালনাগাদ"},
        )

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            log_action(request=request, action="category.update", instance=category)
            messages.success(request, "বিভাগ হালনাগাদ হয়েছে।")
            return redirect("institutes:categories")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "বিভাগ সম্পাদনা", "submit_label": "হালনাগাদ"},
        )
