from pathlib import Path
import environ
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initializing django-environ. Every setting below can come from the
# environment or from investor_app/.env (see .env.example). The defaults are
# for local development and need no credentials at all.
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR,'.env'))

# Brapi API token. Optional: a few tickers (e.g. PETR4, VALE3) and the quote
# list work without one.
BRAPI_KEY = env('BRAPI_KEY', default='')
BRAPI_BASE_URL = env('BRAPI_BASE_URL', default='https://brapi.dev/api')
BRAPI_TIMEOUT = env.int('BRAPI_TIMEOUT', default=30)  # seconds

# Email automation configurations. Without SMTP settings, e-mails are printed
# to the console instead of sent.
EMAIL_BACKEND = env('EMAIL_BACKEND', default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env('EMAIL_HOST', default="smtp.gmail.com")
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER=env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD=env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'smart-investor@localhost')
# Recipient of the price alerts (there are no user accounts yet).
EMAIL_TEST = env('EMAIL_TEST', default='')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-local-development-only')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'rest_framework',
    "market"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'investor_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'investor_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# SQLite by default; docker-compose sets DATABASE_URL to PostgreSQL.
# local.sqlite3 is git-ignored (db.sqlite3 is an old development database
# that was committed, and is no longer used).
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'local.sqlite3'}"),
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery configurations 

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

# Config Django frontend 

X_FRAME_OPTIONS = 'SAMEORIGIN'  
SILENCED_SYSTEM_CHECKS = ["security.W019"]

# The API has no user accounts yet, so it is open, as before; pagination keeps
# /assets/ (about 2000 quotes) responsive.
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {'market': {'handlers': ['console'], 'level': env('LOG_LEVEL', default='INFO')}},
}
