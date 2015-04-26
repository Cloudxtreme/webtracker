# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
        url(r'^$', 'home.views.home', name='index'),
        url(r'^home$', 'home.views.home', name='home'),
        url(r'^report$', 'home.views.track_report', name='track_report'),
        url(r'^trackvisitor$', 'home.views.trackvisitor', name='trackvisitor'),

        url(r'^admin/', include(admin.site.urls)),
)
