"""
Django settings for GuideBuddy.

Settings that differ between development and production come from environment variables
(see the README). Without any variables everything runs in development mode.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


def env_list(name, default):
    value = os.environ.get(name)
    items = value.split(",") if value else default
    return [item.strip() for item in items if item.strip()]


# Mode and secrets
# DJANGO_DEBUG=0 switches to production mode (secure cookies, HSTS, ...)
DEBUG = env_bool("DJANGO_DEBUG", True)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set in production (DJANGO_DEBUG=0)."
        )
    SECRET_KEY = "django-insecure-REPLACE-before-going-live"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "[::1]"])

# Public address of the Nuxt frontend (for links in e-mails)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "simple_history",
    "guides",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

if not DEBUG:
    # In production WhiteNoise serves the static files (after "collectstatic").
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "backend.wsgi.application"


# Database (SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # Put it on a persistent volume in production (DJANGO_DB_PATH)
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
        "OPTIONS": {
            # Lock for writing right away instead of failing late ("database is locked")
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
            # WAL: readers do not block writers (and vice versa)
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}

# Folder for backups (command: python manage.py backup_db)
BACKUP_DIR = Path(os.environ.get("DJANGO_BACKUP_DIR", BASE_DIR / "backups"))


# Passwords and accounts
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Lifetime of confirmation and reset links (seconds): 24 hours
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

# New accounts may only write this many hours after confirming their e-mail address.
# 0 (immediately) in development, 24 by default in production. Moderators are exempt.
NEW_ACCOUNT_WAIT_HOURS = int(os.environ.get("NEW_ACCOUNT_WAIT_HOURS", 0 if DEBUG else 24))


# Language and time
LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # target of "collectstatic" (production)
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Login / logout (only for the Django admin and the old pages)
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "guides:home"
LOGOUT_REDIRECT_URL = "guides:home"


# REST API (Django REST Framework)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["guides.auth.SoftJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Rate limits against spam and password guessing (per IP address)
    "DEFAULT_THROTTLE_RATES": {
        "auth": "30/hour",  # login, confirm, new password, delete account
        "register": "10/hour",  # registration
        "mail": "5/hour",  # request e-mails (resend, forgot password)
        "report": "10/hour",  # reports
        "comment": "10/hour",  # comments
        "write": "60/hour",  # create and edit guides, upload images
        "preview": "1500/hour",  # live preview while writing (Markdown rendering only)
    },
}

# JWT: short-lived access token, longer-lived refresh token with rotation and a blocklist.
# The Nuxt server keeps both in HttpOnly cookies. Lifetimes in minutes and days.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_MINUTES", 10))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", 14))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # A password change invalidates all earlier tokens
    "CHECK_REVOKE_TOKEN": True,
    "REVOKE_TOKEN_CLAIM": "hash_password",
}

# Number of proxies in front (the Nuxt server, plus Nginx if used). They set
# X-Forwarded-For, so the rate limits see the real visitor address.
NUM_PROXIES = int(os.environ.get("DJANGO_NUM_PROXIES", 1))

# Frontend origins that may call the API directly from the browser (development only;
# normally the browser only talks to Nuxt)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", ["http://localhost:3000", "http://127.0.0.1:3000"]
)

# Optional captcha (Cloudflare Turnstile). Empty = off.
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")


# E-mail
# Without EMAIL_HOST, e-mails appear in the terminal of the Django server (development).
# Set EMAIL_HOST (and credentials) as environment variables to really send them.

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "GuideBuddy <noreply@localhost>")

if os.environ.get("EMAIL_HOST"):
    _use_ssl = env_bool("EMAIL_USE_SSL", False)
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": os.environ["EMAIL_HOST"],
                "port": int(os.environ.get("EMAIL_PORT", 465 if _use_ssl else 587)),
                "username": os.environ.get("EMAIL_HOST_USER", ""),
                "password": os.environ.get("EMAIL_HOST_PASSWORD", ""),
                "use_ssl": _use_ssl,
                "use_tls": not _use_ssl and env_bool("EMAIL_USE_TLS", True),
                "timeout": 10,
            },
        },
    }
else:
    MAILERS = {
        "default": {
            "BACKEND": "guides.mail_backend.ReadableConsoleEmailBackend",
        },
    }


# Security in production (DJANGO_DEBUG=0)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", 3600))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", False)
    # Set to "true" if Django itself should enforce HTTPS (not for the internal calls
    # from Nuxt to http://127.0.0.1 - better do it at the reverse proxy).
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", False)
    if env_bool("DJANGO_BEHIND_PROXY", True):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
