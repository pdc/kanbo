# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('kanbo.hello.views',
    url(r'^login-form$', 'login_form', name='hello-login-form'),
    url(r'^logged-in$', 'logged_in', name='hello-logged-in'),
    url(r'^logon-error$', 'login_error', name='hello-login-error'),
    url(r'^create-user$', 'create_user', name='hello-create-user'),
    url(r'^create-association$', 'create_association', name='hello-create-association'),
    url(r'^delete-association$', 'delete_association', name='hello-delete-association'),
    url(r'^logout$', 'log_out', name='hello-log-out'),
)
