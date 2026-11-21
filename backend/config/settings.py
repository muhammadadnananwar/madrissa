"""Django settings for the Madrasa Management System."""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(env(key, default)).lower() in ("1", "true", "yes", "on")


def env_list(key, default=""):
    return [v.strip() for v in env(key, default).split(",") if v.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me-in-production")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Railway sets RAILWAY_PUBLIC_DOMAIN (e.g. api-production.up.railway.app) for services with a public domain.
RAILWAY_PUBLIC_DOMAIN = env("RAILWAY_PUBLIC_DOMAIN", "")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
if env("RAILWAY_PRIVATE_DOMAIN"):
    ALLOWED_HOSTS.append(env("RAILWAY_PRIVATE_DOMAIN"))
ALLOWED_HOSTS.append("healthcheck.railway.app")  # Railway deploy health checks

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "core",
    "accounts",
    "academics",
    "people",
    "attendance",
    "leaves",
    "lms",
    "liveclasses",
    "exams",
    "hifz",
    "finance",
    "library",
    "hostel",
    "transport",
    "inventory",
    "communication",
    "website",
    "cms",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves /static/ (Django admin CSS) without nginx
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    # Local / docker compose: POSTGRES_* variables. Railway: DATABASE_URL (see below).
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "madrasa"),
        "USER": env("POSTGRES_USER", "madrasa"),
        "PASSWORD": env("POSTGRES_PASSWORD", "madrasa"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(env("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

if env("DATABASE_URL"):
    from urllib.parse import unquote, urlparse

    _db = urlparse(env("DATABASE_URL"))
    DATABASES["default"].update(NAME=_db.path.lstrip("/"), USER=unquote(_db.username or ""), PASSWORD=unquote(_db.password or ""),
                                HOST=_db.hostname or "", PORT=str(_db.port or 5432))

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", "Asia/Karachi")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", BASE_DIR / "media"))  # Railway: mount a volume here
# Serve uploaded files from Django itself (no separate web server on Railway). Set false if a CDN/nginx serves them.
SERVE_MEDIA = env_bool("SERVE_MEDIA", True)
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
            ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_RATES": {"public_forms": "30/hour", "login": "20/minute"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=int(env("JWT_ACCESS_HOURS", "8"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "14"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

from urllib.parse import urlparse as _urlparse  # noqa: E402

# Skip entries that resolved to nothing (e.g. "https://" when a Railway reference like ${{website.RAILWAY_PUBLIC_DOMAIN}}
# is empty because the service has no domain yet or is named differently).
CORS_ALLOWED_ORIGINS = [o.rstrip("/") for o in env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:4321,http://127.0.0.1:4321,http://localhost:4322,http://127.0.0.1:4322")
    if _urlparse(o).scheme and _urlparse(o).netloc]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [*CORS_ALLOWED_ORIGINS, *env_list("CSRF_TRUSTED_ORIGINS", "")]
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")  # Django admin login

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "noreply@madrasa.local")

FRONTEND_URL = env("FRONTEND_URL", "http://localhost:4322")  # portal (password reset links)

# ---- Live class providers -------------------------------------------------
# jitsi (free, no account needed) | google_meet | zoom
LIVE_CLASS_DEFAULT_PROVIDER = env("LIVE_CLASS_DEFAULT_PROVIDER", "jitsi")
JITSI_DOMAIN = env("JITSI_DOMAIN", "meet.jit.si")
# Google Meet via Google Calendar API (OAuth refresh token of the madrasa Google account)
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = env("GOOGLE_REFRESH_TOKEN", "")
GOOGLE_CALENDAR_ID = env("GOOGLE_CALENDAR_ID", "primary")
# Zoom Server-to-Server OAuth app
ZOOM_ACCOUNT_ID = env("ZOOM_ACCOUNT_ID", "")
ZOOM_CLIENT_ID = env("ZOOM_CLIENT_ID", "")
ZOOM_CLIENT_SECRET = env("ZOOM_CLIENT_SECRET", "")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
# Embed Jitsi inside the portal (iframe). Only enable for a self-hosted Jitsi or JaaS;
# public meet.jit.si limits embedded calls, so the portal opens it in a new tab instead.
JITSI_EMBED = env_bool("JITSI_EMBED", JITSI_DOMAIN != "meet.jit.si")
