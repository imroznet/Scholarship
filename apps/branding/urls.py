from django.urls import path

from apps.branding.views import BrandAssetAdminView, BrandingManageView

app_name = "branding"

urlpatterns = [
    path("", BrandingManageView.as_view(), name="manage"),
    path("<int:pk>/asset/<slug:kind>/", BrandAssetAdminView.as_view(), name="asset"),
]
