from django.urls import path

from apps.institutes.views import (
    CategoryCreateView,
    CategoryListView,
    CategoryUpdateView,
    InstituteCreateView,
    InstituteDeactivateView,
    InstituteListView,
    InstituteUpdateView,
)

app_name = "institutes"

urlpatterns = [
    path("", InstituteListView.as_view(), name="list"),
    path("new/", InstituteCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", InstituteUpdateView.as_view(), name="edit"),
    path("<int:pk>/deactivate/", InstituteDeactivateView.as_view(), name="deactivate"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/new/", CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category_edit"),
]
