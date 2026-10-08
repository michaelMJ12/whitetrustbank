"""
Django settings for the Vaultra / White Trust Bank project.

Configured for:
- Local development with SQLite
- Render production with PostgreSQL
- Environment-based secrets and configuration
- WhiteNoise static file serving
- Custom accounts.User authentication
- Gmail SMTP configuration
"""

from pathlib import Path
import os

from dotenv import load_dotenv
import dj_database_url


# ============================================================
# BASE DIRECTORY / ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env locally if it exists.
# On Render, environment variables are provided by Render directly.
load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

# IMPORTANT:
# Set SECRET_KEY in Render Environment Variables.
#
# Local development can use the fallback below, but never rely
# on this fallback for production.
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-only-secret-key-change-me-before-deploying",
)


# DEBUG
#
# Local default: True
# Render: set DEBUG=False
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")


# ALLOWED HOSTS
#
# Local:
#   127.0.0.1,localhost
#
# Render:
#   whitetrustbank.com,www.whitetrustbank.com,
#   your-service.onrender.com
#
# You can override this through the ALLOWED_HOSTS
# environment variable.

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,whitetrustltd.com,www.whitetrustltd.com,whitetrustbank.onrender.com"
    ).split(",")
    if host.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)



# CSRF TRUSTED ORIGINS
#
# Render production should contain:
# https://whitetrustbank.com
# https://www.whitetrustbank.com
#
# Add your Render URL if necessary.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "https://whitetrustltd.com,https://www.whitetrustltd.com,https://whitetrustbank.onrender.com"
    ).split(",")
    if origin.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Local applications
    "accounts",
    "banking",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves static files in production.
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL / APPLICATION CONFIGURATION
# ============================================================

ROOT_URLCONF = "vaultra_project.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Custom banking context processor
                "banking.context_processors.notification_counts",
            ],
        },
    },
]


WSGI_APPLICATION = "vaultra_project.wsgi.application"

ASGI_APPLICATION = "vaultra_project.asgi.application"


# ============================================================
# DATABASE
# ============================================================

# Local development:
#   SQLite is used when DATABASE_URL is not available.
#
# Render production:
#   Render PostgreSQL provides DATABASE_URL automatically
#   when the database is connected to the web service.

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# CUSTOM USER / AUTHENTICATION
# ============================================================

AUTH_USER_MODEL = "accounts.User"


# Login authenticates by email through the custom backend.
# Django ModelBackend remains available for Django admin and
# standard username/password authentication.
AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]


LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "banking:dashboard"

LOGOUT_REDIRECT_URL = "landing"


# ============================================================
# GMAIL / EMAIL CONFIGURATION
# ============================================================

# Gmail SMTP configuration.
#
# NOTE:
# Render Free may block outbound SMTP connections.
# If SMTP does not work on Render, use Gmail API or an HTTP
# email provider instead.

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"

EMAIL_PORT = 587

EMAIL_USE_TLS = True


# Gmail address used to send application emails.
#
# Render environment variable:
#
# GMAIL_EMAIL=yourbank@gmail.com
#
EMAIL_HOST_USER = os.environ.get(
    "GMAIL_EMAIL",
    "",
)


# Gmail App Password.
#
# IMPORTANT:
# This must be a Google App Password,
# NOT your normal Gmail password.
#
# Render environment variable:
#
# GMAIL_APP_PASSWORD=abcdefghijklmnop
#
EMAIL_HOST_PASSWORD = os.environ.get(
    "GMAIL_APP_PASSWORD",
    "",
)


# Address shown in the From field.
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)


# Prevent failed email connections from hanging
# the web request indefinitely.
EMAIL_TIMEOUT = 20


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

# Existing source static directory.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# collectstatic output directory.
STATIC_ROOT = BASE_DIR / "staticfiles"


# WhiteNoise storage.
#
# Django 4.2 supports the STORAGES setting.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# SECURITY / HTTPS
# ============================================================

# Secure cookies automatically when DEBUG=False.
CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SECURE = not DEBUG


# Keep False initially while configuring Render/custom domain.
# Once HTTPS is confirmed to work correctly, this can be changed
# to True.
SECURE_SSL_REDIRECT = False


# Tell Django that Render's reverse proxy is handling HTTPS.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# DJANGO MESSAGES
# ============================================================

MESSAGE_TAGS = {}