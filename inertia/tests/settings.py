from pathlib import Path

from pydantic import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class InertiaSettings(BaseSettings):
    """Inertia settings for FastAPI."""

    # The Inertia template layout to use
    INERTIA_LAYOUT: str = "layout.html"

    # The Inertia version string for cache busting
    INERTIA_VERSION: str = "1.0"

    # The path to the templates directory
    TEMPLATES_DIR: Path = BASE_DIR / "tests/templates"

    # Path to the SSR bundle (if using SSR)
    SSR_BUNDLE_PATH: str = ""

    # Whether to enable SSR
    SSR_ENABLED: bool = False

    # Maximum SSR timeout in seconds
    SSR_TIMEOUT: int = 10

    # Secret key for CSRF protection
    SECRET_KEY: str = "fastapi-insecure-key-for-testing-only"

    class Config:
        env_prefix = "INERTIA_"


# Create a default settings instance
settings = InertiaSettings()

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "inertia.middleware.InertiaMiddleware",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "inertia",
    "inertia.tests.testapp.apps.TestAppConfig",
]

ROOT_URLCONF = "inertia.tests.testapp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "tests/testapp",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# only in place to silence an error
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "unused"}}

# silence a warning
USE_TZ = False
