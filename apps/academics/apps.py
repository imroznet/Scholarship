from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.academics"
    verbose_name = "Academics"

    def ready(self):
        from . import signals  # noqa: F401
