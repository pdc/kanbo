from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'kanbo.views.home', name='home'),
    # url(r'^kanbo/', include('kanbo.foo.urls')),

    url(r'^$', 'kanbo.about.views.home', name='home'),

    # Enable logging in with myriad social network sites:
    url(r'', include('social_auth.urls')),
    url(r'^hello/', include('kanbo.hello.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin', include(admin.site.urls)),

    # Because user name is a wildcard it comes last.
    url(r'', include('kanbo.board.urls')),
)
