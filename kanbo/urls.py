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

    # Because user name is a wildcard it comes last.
    url(r'^', include('kanbo.board.urls')),
]

# urlpatterns = patterns('',
#     # Examples:
#     # url(r'^$', 'kanbo.views.home', name='home'),
#     # url(r'^kanbo/', include('kanbo.foo.urls')),

#     url(r'^$', 'kanbo.about.views.home', name='home'),

#     # Enable logging in with myriad social network sites:
#     url(r'', include('social_auth.urls')),
#     url(r'^hello/', include('kanbo.hello.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    # url(r'^admin', include(admin.site.urls)),

    # # Because user name is a wildcard it comes last.
    # url(r'', include('kanbo.board.urls')),
# )
