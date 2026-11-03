from django.urls import path

from apps.academics.views import ClassCreateView, ClassListView, ClassUpdateView, RegistrationControlView

app_name = "academics"

urlpatterns = [
    path("classes/", ClassListView.as_view(), name="classes"),
    path("classes/new/", ClassCreateView.as_view(), name="class_create"),
    path("classes/<int:pk>/edit/", ClassUpdateView.as_view(), name="class_edit"),
    path("registration/", RegistrationControlView.as_view(), name="registration"),
]
