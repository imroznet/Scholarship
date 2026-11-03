from django.urls import path

from apps.accounts.views import PasswordChangePage, ScholarshipLoginView, ScholarshipLogoutView

app_name = "accounts"

urlpatterns = [
    path("login/", ScholarshipLoginView.as_view(), name="login"),
    path("logout/", ScholarshipLogoutView.as_view(), name="logout"),
    path("password/", PasswordChangePage.as_view(), name="password"),
]
