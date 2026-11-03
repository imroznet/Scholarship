from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from apps.accounts.forms import OperatorForm, StyledAuthenticationForm, StyledPasswordChangeForm
from apps.accounts.mixins import SuperAdminRequiredMixin
from apps.accounts.models import User
from apps.accounts.throttling import (
    clear_login_failures,
    client_ip,
    is_login_locked,
    record_failed_login,
)
from apps.audit.services import log_action


class ScholarshipLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        self.lock_message = ""
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "")
        ip_address = client_ip(request)
        if username and is_login_locked(username, ip_address):
            form = self.get_form()
            form.add_error(None, "অনেকবার ভুল চেষ্টা হয়েছে। কিছুক্ষণ পরে আবার চেষ্টা করুন।")
            self.lock_message = "locked"
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        if not self.lock_message:
            username = self.request.POST.get("username", "")
            if username:
                record_failed_login(username, client_ip(self.request))
            log_action(
                request=self.request,
                action="login.failed",
                target_model="accounts.User",
                target_repr=username[:150],
            )
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        clear_login_failures(user.username, client_ip(self.request))
        login(self.request, user)
        log_action(request=self.request, action="login.success", instance=user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return super().get_success_url()


class ScholarshipLogoutView(LogoutView):
    pass


class PasswordChangePage(PasswordChangeView):
    template_name = "accounts/password.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        messages.success(self.request, "পাসওয়ার্ড পরিবর্তন হয়েছে।")
        log_action(request=self.request, action="password.change", instance=self.request.user)
        return super().form_valid(form)


class OperatorListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        operators = User.objects.filter(role=User.Role.DATA_ENTRY_OPERATOR).order_by("username")
        return render(request, "accounts/user_list.html", {"operators": operators, "page_title": "অ্যাডমিন ব্যবস্থাপনা"})


class OperatorCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": OperatorForm(), "page_title": "অপারেটর যোগ", "submit_label": "সংরক্ষণ"},
        )

    def post(self, request):
        form = OperatorForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request=request, action="operator.create", instance=user)
            messages.success(request, "অপারেটর তৈরি হয়েছে।")
            return redirect("users:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "অপারেটর যোগ", "submit_label": "সংরক্ষণ"},
        )


class OperatorEditView(SuperAdminRequiredMixin, View):
    def _operator(self, pk):
        return get_object_or_404(User, pk=pk, role=User.Role.DATA_ENTRY_OPERATOR)

    def get(self, request, pk):
        operator = self._operator(pk)
        form = OperatorForm(
            instance=operator,
            initial={
                "username": operator.username,
                "first_name": operator.first_name,
                "last_name": operator.last_name,
                "email": operator.email,
                "phone": operator.phone,
                "is_active": operator.is_active,
            },
        )
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "অপারেটর সম্পাদনা", "submit_label": "হালনাগাদ"},
        )

    def post(self, request, pk):
        operator = self._operator(pk)
        form = OperatorForm(request.POST, instance=operator)
        if form.is_valid():
            user = form.save()
            log_action(request=request, action="operator.update", instance=user, changes={"is_active": user.is_active})
            messages.success(request, "অপারেটরের তথ্য হালনাগাদ হয়েছে।")
            return redirect("users:list")
        return render(
            request,
            "dashboard/simple_form.html",
            {"form": form, "page_title": "অপারেটর সম্পাদনা", "submit_label": "হালনাগাদ"},
        )
