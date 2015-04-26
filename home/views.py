#!/usr/bin/python
# -*- coding: utf-8 -*-
# from msilib.schema import tables

from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from models import Visitor, Ip, Organization
from tasks import whois_handler
from whois_tracker.db_manager import dict_fetchall
from django.db import connection


# To track ip next script must be inserted into html page:
# <script  type="text/javascript">
#     pageUrl = encodeURI(window.location.href)
#     document.write('<script type="text\/javascript" src="http:\/\/dsyhan.pythonanywhere.com\/trackvisitor?url=' + pageUrl + '">');
#     document.write('<\/script>');
# </script>
# or
# <script  type="text/javascript">
#     pageUrl = encodeURI(window.location.href)
#     document.write('<script type="text\/javascript" src="http:\/\/127.0.0.1:8000\/trackvisitor?url=' + pageUrl + '">');
#     document.write('<\/script>');
# </script>


def home(request, template_name="home.html"):
    # rs = Ip.objects.extra(tables=['wt_organization'])
    # print rs
    sql_txt = """select
        ORG.id as organization_id, ORG.organization_name, ORG.organization_address, ORG.country,
        IP.id as ip_id, IP.ip_address,
        VIS.id as visitor_id,
        VIS.page_url,
        VIS.referer_url,
        VIS.datetime_of_visit
    from wt_ip IP left outer join wt_organization ORG on IP.organization_id = ORG.id
        left outer join wt_visitor VIS on IP.id = VIS.ip_id
    order by VIS.page_url, VIS.datetime_of_visit;
    """

    cursor = connection.cursor()
    cursor.execute(sql_txt)
    rs = dict_fetchall(cursor)

    return render(request, template_name, {'rows': rs})


def track_report(request, template_name="track_report.html"):
    # rs = Ip.objects.extra(tables=['wt_organization'])
    # print rs
    sql_txt = """select
        ORG.id as organization_id, ORG.organization_name, ORG.organization_address, ORG.country,
        IP.ip_address,
        VIS.page_url,
        VIS.referer_url,
        count(*) as visits_count
     from wt_ip IP left outer join wt_organization ORG on IP.organization_id = ORG.id
        left outer join wt_visitor VIS on IP.id = VIS.ip_id
    group by ORG.id, ORG.organization_name, ORG.organization_address, ORG.country,
        IP.ip_address,
        VIS.page_url,
        VIS.referer_url;
    """

    cursor = connection.cursor()
    cursor.execute(sql_txt)
    rs = dict_fetchall(cursor)

    return render(request, template_name, {'rows': rs})


def trackvisitor(request, template_name=None):
    visitor_ip = extract_ip(request)
    referer_url = request.META.get('HTTP_REFERER', '')
    page_url = request.GET['url']
    assert len(visitor_ip) <= Ip._meta.get_field('ip_address').max_length
    maxlen_referer_url = Visitor._meta.get_field('referer_url').max_length
    if len(referer_url) > maxlen_referer_url:
        referer_url = referer_url[:maxlen_referer_url]

    maxlen_page_url = Visitor._meta.get_field('page_url').max_length
    if len(page_url) > maxlen_page_url:
        page_url = page_url[:maxlen_page_url]

    whois_handler(visitor_ip, referer_url, page_url, datetime.now())
    # whois_handler.delay(visitor_ip, referer_url, page_url, datetime.now())

    # ip_txt = "document.write('Visitor: ip_address: %s, Referer url: %s, page url: %s');" % (visitor_ip, referer_url, page_url)
    ip_txt = ''
    return HttpResponse(ip_txt)


def extract_ip(request):
    """
    read ip address and referrer url from request
    :param request: request
    :return: <ip address>, <referrer url>
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        visitor_ip = (
            x_forwarded_for.split(',')[0]).strip()  #X-Forwarded-For format: client_ip, proxy1_ip, proxy2_ip, ...
    else:
        visitor_ip = request.META.get('REMOTE_ADDR')

    return visitor_ip


# def dict_fetchall(cursor):
#     """Returns all rows from a cursor as a dictionary pairs (field name, field value)
#     """
#     desc = cursor.description
#     return [
#         dict(zip([col[0] for col in desc], row))
#         for row in cursor.fetchall()
#     ]

