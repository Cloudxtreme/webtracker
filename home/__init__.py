#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

# try:
#     from webtracker.celery import app as celery_app
# except ImportError:
#     app = None