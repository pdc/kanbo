# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin
import kanbo.about.views


admin.autodiscover()


urlpatterns = [
    url(r'^$', kanbo.about.views.home, name='home'),

    # Enable logging in with myriad social network sites:
    url(r'', include('social_auth.urls')),
    url(r'^hello/', include('kanbo.hello.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin', include(admin.site.urls)),

    url(r'^about/check-env', kanbo.about.views.check_env),

    # Because user name is a wildcard it comes last.
    url(r'^', include('kanbo.board.urls')),
]