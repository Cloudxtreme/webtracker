# -*- coding: utf-8 -*-

"""
Django settings for webtracker project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ukze1z6p2s-z8qfqu)tl&y*ytn8%#82et_spc-=q_q1q55x8te'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'home',
)

try:
    from celery import Celery

    # import djcelery
    # djcelery.setup_loader()

    # INSTALLED_APPS += (
    #     'djcelery',
    #     # 'kombu.transport.django', #django transport for Celery
    # )

    # Django database as brocker and backend
    # CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
    # BROKER_URL = 'django://'

    # RabbitMQ as broker
    # BROKER_URL = 'amqp://guest:guest@localhost:5672//'
    # Redis
    BROKER_URL = 'redis://localhost:6379/0'
    # CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
except ImportError:
    pass

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webtracker.urls'

WSGI_APPLICATION = 'webtracker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dsyhan$webtracker',  # Or path to database file if using sqlite3.
        'USER': 'dsyhan',  # Not used with sqlite3.
        'PASSWORD': 'site_rank',  # Not used with sqlite3.
        'HOST': '127.0.0.1',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {"init_command": "SET storage_engine=INNODB", },
        # DATABASE_OPTIONS = { "init_command": "SET storage_engine=INNODB, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED", }
    }
}

# parameters for direct connection to database for pythonanywhere
DB_PARMS = {'host': "mysql.server",
            'user': "dsyhan",
            'passwd': "site_rank",
            'db': "dsyhan$webtracker",
            'charset': 'utf8',
            'port': 3306}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR,  'templates'),
)


# whois tracker can be launched as separate application via scheduler or put to Celery task queue
# WHOIS_MODE = 'debug'
WHOIS_MODE = 'scheduler'
# WHOIS_MODE = 'task queue' # Celery

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
try:
    from local_settings import *
except ImportError:
    pass

# try:
#     from test_settings import *
# except ImportError:
#     pass
