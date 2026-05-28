"""
POS Tizim — Cross-Platform Settings
=====================================
Windows, macOS, Linux da ishlaydi.
"""
import sys
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ── CORE ───────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production-min-50-chars!!')
DEBUG      = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'pos_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'pos_app.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'frontend'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'backend.wsgi.application'

# ── DATABASE ───────────────────────────────────────────────
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
    except ImportError:
        raise ImportError("pip install dj-database-url")
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {'timeout': 20},
        }
    }

# ── CACHE ──────────────────────────────────────────────────
CACHE_URL = config('CACHE_URL', default=None)
if CACHE_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': CACHE_URL,
            'TIMEOUT': 300,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'pos-cache',
            'TIMEOUT': 300,
        }
    }

# ── SESSION — simple db, works on all platforms ────────────
# cached_db requires BOTH cache + session table synced — fragile on Windows
SESSION_ENGINE          = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE      = 86400
SESSION_COOKIE_HTTPONLY = True

# ── REST FRAMEWORK ─────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES':   ['rest_framework.parsers.JSONParser'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('THROTTLE_ANON', default='600/hour'),
        'user': config('THROTTLE_USER', default='2000/hour'),
        'sell': config('THROTTLE_SELL', default='200/minute'),
    },
    'EXCEPTION_HANDLER': 'pos_app.exceptions.custom_exception_handler',
}

# ── CORS ───────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL', default=DEBUG, cast=bool)
CORS_ALLOWED_ORIGINS   = config('CORS_ALLOWED_ORIGINS', default='http://localhost:8000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ── STATIC FILES ───────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Avoid "Source and destination are the same" error on Windows
_frontend_dir = BASE_DIR / 'frontend'
if _frontend_dir.exists() and _frontend_dir.resolve() != STATIC_ROOT.resolve():
    STATICFILES_DIRS = [_frontend_dir]
else:
    STATICFILES_DIRS = []

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── SECURITY (production only) ─────────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    X_FRAME_OPTIONS                = 'DENY'
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    SECURE_SSL_REDIRECT            = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# ── LOGGING — cross-platform, graceful fallback ────────────
LOGS_DIR = BASE_DIR / 'logs'
_log_handlers = {'console': {
    'class': 'logging.StreamHandler',
    'formatter': 'simple',
    'stream': 'ext://sys.stdout',
}}
_app_handlers   = ['console']
_error_handlers = ['console']
_sales_handlers = ['console']

try:
    LOGS_DIR.mkdir(exist_ok=True)

    def _make_rotating(filename, level=None, max_mb=10, backup=5):
        h = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / filename),   # str() for Windows compat
            'maxBytes': max_mb * 1024 * 1024,
            'backupCount': backup,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        }
        if level:
            h['level'] = level
        return h

    _log_handlers['file_app']   = _make_rotating('app.log')
    _log_handlers['file_error'] = _make_rotating('error.log', level='ERROR')
    _log_handlers['file_sales'] = _make_rotating('sales.log', max_mb=20, backup=10)
    _app_handlers   = ['console', 'file_app', 'file_error']
    _error_handlers = ['console', 'file_error']
    _sales_handlers = ['console', 'file_sales']
except Exception:
    pass  # No log files — console only, completely fine

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name} — {message}', 'style': '{'},
        'simple':  {'format': '[{asctime}] {levelname} — {message}', 'style': '{'},
    },
    'handlers': _log_handlers,
    'loggers': {
        'django':        {'handlers': _error_handlers, 'level': 'WARNING',                     'propagate': False},
        'pos_app':       {'handlers': _app_handlers,   'level': 'DEBUG' if DEBUG else 'INFO',   'propagate': False},
        'pos_app.sales': {'handlers': _sales_handlers, 'level': 'INFO',                        'propagate': False},
    },
}

# ── I18N / TIMEZONE ────────────────────────────────────────
LANGUAGE_CODE      = 'uz'
TIME_ZONE          = 'Asia/Tashkent'
USE_I18N           = True
USE_TZ             = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── APP-SPECIFIC ───────────────────────────────────────────
CURRENCY_CACHE_TTL     = config('CURRENCY_CACHE_TTL',     default=300,   cast=int)
CURRENCY_FALLBACK_RATE = config('CURRENCY_FALLBACK_RATE', default=12800, cast=int)
CURRENCY_API_TIMEOUT   = config('CURRENCY_API_TIMEOUT',   default=6,     cast=int)
