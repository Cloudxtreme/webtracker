#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
from django.conf import settings

try:
    from celery import Celery

    # How to start celery:
    # C:\Users\psa\ve_webtracker\lib\site-packages\celery\apps\worker.py

    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webtracker.settings')

    app = Celery('webtracker')

    # app.conf.update(
    #     CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
    # )
    #
    # app.conf.update(
    #     BROKER_URL = 'django://'
    # )


    # app = Celery('webtracker',
    #          broker='redis://',
    #          backend='redis://',
    #          include=['home.tasks'])
    #


    # Using a string here means the worker will not have to
    # pickle the object when using Windows.
    app.config_from_object('django.conf:settings')
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


    @app.task(bind=True)
    def debug_task(self):
        print('Request: {0!r}'.format(self.request))
except ImportError:
    pass