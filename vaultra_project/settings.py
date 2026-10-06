
"""
Django settings for the Vaultra bank project.

This is a straightforward, single-server Django setup (SQLite, synchronous
views, session auth) meant to be a solid, correct starting point — not a
finished, hardened production deployment.

Search "PRODUCTION NOTE" in this file for the handful of things you must
change before shipping this for real (SECRET_KEY, DEBUG, database, HTTPS
settings, email backend).
"""

from pathlib import Path
import os


SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "whitetrustbank.com",
    "www.whitetrustbank.com",
    ".onrender.com",
]


BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

# PRODUCTION NOTE:
# Load this from an environment variable / secrets manager.
# Never commit a real secret key to source control.
SECRET_KEY = os.environ.get(
    "VAULTRA_SECRET_KEY",
    "dev-only-secret-key-change-me-before-deploying",
)


# PRODUCTION NOTE:
# Default to False in production.
# Set VAULTRA_DEBUG=1 only during development.
DEBUG = os.environ.get("VAULTRA_DEBUG", "1") == "1"


ALLOWED_HOSTS = os.environ.get(
    "VAULTRA_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")


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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
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

# PRODUCTION NOTE:
# Swap SQLite for PostgreSQL/MySQL in production.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Example MySQL configuration
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "whitetru_vaultra_db",
#         "USER": "whitetru_vaultra_user",
#         "PASSWORD": os.environ.get("VAULTRA_DB_PASSWORD"),
#         "HOST": "localhost",
#         "PORT": "3306",
#         "OPTIONS": {
#             "charset": "utf8mb4",
#         },
#     },
# }


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


# Login authenticates by email (see accounts/backends.py).
# ModelBackend stays second so createsuperuser's username/password
# still works for /django-admin/.
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

# Gmail SMTP server
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Gmail address used to send application emails.
#
# Example:
# GMAIL_EMAIL=yourbank@gmail.com
EMAIL_HOST_USER = os.environ.get("GMAIL_EMAIL", "")


# Gmail App Password.
#
# IMPORTANT:
# This must be a Google App Password, NOT your normal Gmail password.
#
# Example:
# GMAIL_APP_PASSWORD=abcdefghijklmnop
EMAIL_HOST_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


# Address shown in the "From" field.
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)


# Optional email timeout.
# Prevents a failed Gmail connection from hanging the request indefinitely.
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

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# PRODUCTION NOTE:
# `python manage.py collectstatic` writes files here.


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# SECURITY / HTTPS
# ============================================================

# These only take effect when DEBUG=False behind HTTPS.

CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SECURE = not DEBUG

SECURE_SSL_REDIRECT = False

# PRODUCTION NOTE:
# Change to True after HTTPS/TLS is correctly configured.
#
# SECURE_SSL_REDIRECT = True


# ============================================================
# DJANGO MESSAGES
# ============================================================

MESSAGE_TAGS = {}
