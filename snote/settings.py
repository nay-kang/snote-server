"""
Django settings for snote project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJ_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv('PROD','')!='true' else False
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    'rest_framework_simplejwt.token_blacklist',
    'daphne',
    'corsheaders',
    'core',
]

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # 'DEFAULT_PERMISSION_CLASSES':[],
    'UNAUTHENTICATED_USER':None,
}

CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    'content-encoding'
]

ROOT_URLCONF = 'snote.urls'

WSGI_APPLICATION = 'snote.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REDIS_CHANNEL_DB = 1
REDIS_CACHE_DB = 0
REDIS_STORAGE_DB = 2

ASGI_APPLICATION = "snote.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://{os.getenv('REDIS_HOST')}:6379/{REDIS_CHANNEL_DB}"],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND":"django_redis.cache.RedisCache",
        "LOCATION":f"redis://{os.getenv('REDIS_HOST')}:6379/{REDIS_CACHE_DB}",
        "OPTIONS":{
            "CLIENT_CLASS":"django_redis.client.DefaultClient"
        }
    },
    "redis_db": {
        "BACKEND":"django_redis.cache.RedisCache",
        "LOCATION":f"redis://{os.getenv('REDIS_HOST')}:6379/{REDIS_STORAGE_DB}",
        "OPTIONS":{
            "CLIENT_CLASS":"django_redis.client.DefaultClient"
        }
    }
}

AUTH_USER_MODEL = "core.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=2),  # Longer access token for better UX
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),  # 30 days refresh token
    "ROTATE_REFRESH_TOKENS": True,  # Enable rotation for security
    "BLACKLIST_AFTER_ROTATION": False,  # No need for blacklist if we trust refresh tokens
    # "UPDATE_LAST_LOGIN": True,  # Track last login
    "TOKEN_OBTAIN_SERIALIZER": "core.serializers.SnoteTokenObtainPairSerializer",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(hours=1),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=30),
}
AUTHENTICATION_BACKENDS = [
    'core.auth_backend.OTPBackend',
]

def get_bool_env(key: str, default: bool = False) -> bool:
    """Convert environment string variable to bool."""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'y', 'on')

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = get_bool_env('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = get_bool_env('EMAIL_USE_SSL', False)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'