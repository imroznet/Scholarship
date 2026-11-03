from django.apps import AppConfig


class SessionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sessions"
    label = "scholarship_sessions"
    verbose_name = "Scholarship sessions"

    def ready(self):
        from . import signals  # noqa: F401
