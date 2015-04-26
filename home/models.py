#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

# select
# 	ORG.id as organization_id, ORG.organization_name, ORG.organization_address, ORG.country,
# 	IP.id as ip_id, IP.ip_address,
# 	VIS.id as visitor_id,
# 	VIS.page_url,
# 	VIS.referer_url,
# 	VIS.datetime_of_visit
#  from wt_ip IP left outer join wt_organization ORG on IP.organization_id = ORG.id
# 	left outer join wt_visitor VIS on IP.id = VIS.ip_id;


class Organization(models.Model):
    organization_name = models.CharField(max_length=200)
    organization_address = models.CharField(max_length=1000)
    country = models.CharField(max_length=2)

    def __str__(self):
        return self.organization_name

    class Meta:
        db_table = 'wt_organization'
        unique_together = ('country', 'organization_name')


# this intermedia table is introduced to support integrity constraint: organization can't have dupe ip's
class Ip(models.Model):
    organization = models.ForeignKey(Organization, null=True)
    ip_address = models.CharField(max_length=15)

    class Meta:
        db_table = 'wt_ip'
        unique_together = ('organization', 'ip_address')


class Visitor(models.Model):
    referer_url = models.CharField(max_length=1000, default='')
    page_url = models.CharField(max_length=1000)
    datetime_of_visit = models.DateTimeField()
    ip = models.ForeignKey(Ip)

    class Meta:
        db_table = 'wt_visitor'


class VisitorQueue(models.Model):
    visitor_ip = models.CharField(max_length=15)
    referer_url = models.CharField(max_length=1000, default='')
    page_url = models.CharField(max_length=1000)
    datetime_of_visit = models.DateTimeField()

    class Meta:
        db_table = 'wt_visitor_queue'


class QueueLock(models.Model):
    lock_on = models.BooleanField()

    class Meta:
        db_table = 'wt_queue_lock'
