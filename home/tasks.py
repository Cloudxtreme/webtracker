#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
try:
    #from celery import task
    from celery import shared_task
except ImportError:
    def shared_task(f):
        return f
    # def shared_task():
    #     def wrapper(f):
    #         return f
    #     return wrapper

from whois_tracker.db_manager import DbManager
from whois_tracker.whois_exception import WtWhoisException, WhoisParserException, UnknownWhoisServer, UnknownWhoisFormat
from whois_tracker.messanger import send_whois_message
from whois_tracker.whois import WhoisTracker
import webtracker.settings as settings
import logging
from home.models import VisitorQueue


LOG_FILENAME = 'webtracker.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class WebtrackerError(Exception):
    pass


whois_handler = None

def whois_handler_schedule(visitor_ip, referer_url, page_url, datetime_of_visit):
    rec = VisitorQueue(visitor_ip=visitor_ip,
                       referer_url=referer_url,
                       page_url=page_url,
                       datetime_of_visit=datetime_of_visit)
    rec.save()


def whois_handler_delay(visitor_ip, referer_url, page_url, date_time_of_visit):
    find_whois.delay(visitor_ip, referer_url, page_url, date_time_of_visit)


def whois_handler_debug(visitor_ip, referer_url, page_url, date_time_of_visit):
    find_whois(visitor_ip, referer_url, page_url, date_time_of_visit)


@shared_task
def find_whois(visitor_ip, referer_url, page_url, date_time_of_visit):
    ws = WhoisTracker()
    dbman = DbManager()
    dbman.connect()
    try:
        try:
            nac = ws.search_whois(visitor_ip)
            assert nac is not None
            nac_org_id = dbman.append_new_org(*nac)
        except WtWhoisException as e:
            send_whois_message(e, visitor_ip, page_url, date_time_of_visit)
            nac_org_id = None
            nac = None

        ip_id = dbman.append_new_ip(visitor_ip, nac_org_id)
        dbman.append_visitor(referer_url, page_url, date_time_of_visit, ip_id)
    finally:
        dbman.close()

    return 'ip: %s' % visitor_ip


# @task()
# def add(x, y):
#     return x + y

if settings.WHOIS_MODE == 'scheduler':
    whois_handler = whois_handler_schedule
elif settings.WHOIS_MODE == 'task queue':
    whois_handler = whois_handler_delay
elif settings.WHOIS_MODE == 'debug':
    whois_handler = whois_handler_debug
else:
    whois_handler = None
    logging.debug('Unknown WHOIS_MODE from settings.py: %s' % settings.WHOIS_MODE)
#    raise WebtrackerError('Unknown WHOIS_MODE from settings.py: %s' % settings.WHOIS_MODE)