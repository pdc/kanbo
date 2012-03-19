from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'kanbo.views.home', name='home'),
    # url(r'^kanbo/', include('kanbo.foo.urls')),
    
    url(r'^$', 'apps.about.views.home', name='home'),
    url(r'^boards/', include('apps.stories.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
