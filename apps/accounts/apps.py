from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"

    def ready(self):
        from django.contrib import admin

        def has_permission(request):
            user = request.user
            return bool(user.is_authenticated and user.is_active and user.is_super_admin)

        admin.site.has_permission = has_permission
        admin.site.site_header = "Scholarship administration"
        admin.site.site_title = "Scholarship"
