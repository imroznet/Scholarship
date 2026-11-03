from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import BASE_DIR, DATABASES, LOGGING, env

DEBUG = False
if env.bool("DEBUG", default=False):
    raise ImproperlyConfigured("DEBUG must stay off when production settings are loaded.")

SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY or SECRET_KEY.startswith("dev-") or len(SECRET_KEY) < 40:
    raise ImproperlyConfigured("Set a unique SECRET_KEY of at least 40 characters.")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]:
    raise ImproperlyConfigured("Set ALLOWED_HOSTS to the real domain names.")

database_url = env("DATABASE_URL", default="")
if not database_url or database_url.startswith("sqlite"):
    raise ImproperlyConfigured(
        "Production requires PostgreSQL or MySQL through DATABASE_URL. SQLite is not allowed."
    )
DATABASES["default"] = env.db("DATABASE_URL")
if "mysql" in DATABASES["default"]["ENGINE"]:
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].setdefault("charset", "utf8mb4")
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

SECURE_SSL = env.bool("DJANGO_SECURE_SSL", default=True)
SESSION_COOKIE_SECURE = SECURE_SSL
CSRF_COOKIE_SECURE = SECURE_SSL
SECURE_SSL_REDIRECT = SECURE_SSL
if env.bool("DJANGO_BEHIND_PROXY", default=True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if SECURE_SSL:
    SECURE_HSTS_SECONDS = env.int("HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

if env("CACHE_BACKEND", default="db") == "db":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "scholarship_cache",
        }
    }

LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))  # noqa: F405
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": str(LOG_DIR / "django.log"),
    "maxBytes": 1024 * 1024 * 5,
    "backupCount": 5,
    "formatter": "plain",
}
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["django.request"]["handlers"] = ["console", "file"]  # noqa: F405
