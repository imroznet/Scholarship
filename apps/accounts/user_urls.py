from django.urls import path

from apps.accounts.views import OperatorCreateView, OperatorEditView, OperatorListView

app_name = "users"

urlpatterns = [
    path("", OperatorListView.as_view(), name="list"),
    path("new/", OperatorCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", OperatorEditView.as_view(), name="edit"),
]
