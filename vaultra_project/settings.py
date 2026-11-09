from pathlib import Path
import os

from dotenv import load_dotenv
import dj_database_url


# ============================================================
# BASE DIRECTORY / ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env file.
# Render environment variables override local configuration.
load_dotenv(BASE_DIR / ".env", override=False)


# ============================================================
# SECURITY / ENVIRONMENT CONFIGURATION
# ============================================================

SECRET_KEY = (
    os.getenv("VAULTRA_SECRET_KEY")
    or os.getenv("SECRET_KEY")
)

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Configure VAULTRA_SECRET_KEY "
        "or SECRET_KEY in your environment."
    )


# ============================================================
# DEBUG
# ============================================================

DEBUG_VALUE = os.getenv(
    "VAULTRA_DEBUG",
    os.getenv("DEBUG", "False"),
)

DEBUG = DEBUG_VALUE.strip().lower() in (
    "true",
    "1",
    "yes",
    "on",
)

# DEBUG = True


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS_VALUE = os.getenv(
    "VAULTRA_ALLOWED_HOSTS",
    os.getenv(
        "ALLOWED_HOSTS",
        (
            "127.0.0.1,localhost,"
            "whitetrustltd.com,"
            "www.whitetrustltd.com,"
            "whitetrustbank.onrender.com"
        ),
    ),
)


ALLOWED_HOSTS = [
    host.strip()
    for host in ALLOWED_HOSTS_VALUE.split(",")
    if host.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if (
    RENDER_EXTERNAL_HOSTNAME
    and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS
):
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)





# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        (
            "https://whitetrustltd.com,"
            "https://www.whitetrustltd.com,"
            "https://whitetrustbank.onrender.com"
        ),
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
# SQLite is used when DATABASE_URL is not available.
#
# Render production:
# Render PostgreSQL provides DATABASE_URL automatically.

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL and not DEBUG:
    raise RuntimeError(
        "DATABASE_URL is required when DEBUG=False."
    )

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

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "banking:dashboard"

LOGOUT_REDIRECT_URL = "landing"


# ============================================================
# GMAIL SMTP / EMAIL CONFIGURATION
# ============================================================

# Gmail SMTP server configuration.
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = "smtp.gmail.com"

EMAIL_PORT = 587

# Gmail SMTP uses STARTTLS on port 587.
EMAIL_USE_TLS = True

EMAIL_USE_SSL = False

# Gmail account used to authenticate with SMTP.
EMAIL_HOST_USER = os.getenv(
    "GMAIL_EMAIL",
    "",
).strip()

# Google App Password.
# Spaces are removed to support Google's grouped display format.
EMAIL_HOST_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD",
    "",
).replace(" ", "").strip()

# Sender address displayed to recipients.
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    f"White Trust Bank <{EMAIL_HOST_USER}>",
).strip()

SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_TIMEOUT = 30

# Do not silently ignore SMTP errors.
# send_mail(..., fail_silently=False) will expose errors.


# ============================================================
# PASSWORD RESET CONFIGURATION
# ============================================================

# Password reset links expire after one hour.
PASSWORD_RESET_TIMEOUT = 3600


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


# ============================================================
# WHITENOISE STORAGE
# ============================================================

# Django 4.2 supports the STORAGES setting.
STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
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

# Keep False until HTTPS and reverse-proxy configuration
# have been verified.
SECURE_SSL_REDIRECT = False

# Tell Django that Render's reverse proxy handles HTTPS.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} "
                "{name} {message}"
            ),
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "WARNING",
    },

    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },

        "django.core.mail": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },

        "accounts": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# ============================================================
# DJANGO MESSAGES
# ============================================================

MESSAGE_TAGS = {}


# ============================================================
# PRODUCTION SECURITY SETTINGS
# ============================================================

# Enable HTTPS-related protection when running in production.
if not DEBUG:

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"

    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

    # Enable HSTS only after confirming HTTPS works correctly.
    # Set these through environment variables when ready.
    SECURE_HSTS_SECONDS = int(
        os.getenv("SECURE_HSTS_SECONDS", "0")
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = (
        os.getenv(
            "SECURE_HSTS_INCLUDE_SUBDOMAINS",
            "False",
        ).lower() in ("true", "1", "yes")
    )

    SECURE_HSTS_PRELOAD = False


# ============================================================
# EMAIL CONFIGURATION VALIDATION
# ============================================================

# These checks intentionally do not print or expose credentials.
# They allow the application to start even if email is not yet
# configured, while making missing settings visible in logs.

if not EMAIL_HOST_USER:
    import logging
    logging.getLogger(__name__).warning(
        "GMAIL_EMAIL is not configured. Email delivery will not work."
    )

if not EMAIL_HOST_PASSWORD:
    import logging
    logging.getLogger(__name__).warning(
        "GMAIL_APP_PASSWORD is not configured. Email delivery will not work."
    )

if (
    EMAIL_HOST_USER
    and DEFAULT_FROM_EMAIL
    and EMAIL_HOST_USER.lower()
    not in DEFAULT_FROM_EMAIL.lower()
):
    import logging
    logging.getLogger(__name__).warning(
        "DEFAULT_FROM_EMAIL differs from GMAIL_EMAIL. "
        "Verify that Gmail permits the sender address."
    )
