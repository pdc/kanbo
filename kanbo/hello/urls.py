# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from django.conf.urls import url
import kanbo.hello.views


urlpatterns = [
    url(r'^login-form$', kanbo.hello.views.login_form, name='hello-login-form'),
    url(r'^logged-in$', kanbo.hello.views.logged_in, name='hello-logged-in'),
    url(r'^logon-error$', kanbo.hello.views.login_error, name='hello-login-error'),
    url(r'^create-user$', kanbo.hello.views.create_user, name='hello-create-user'),
    url(r'^create-association$', kanbo.hello.views.create_association, name='hello-create-association'),
    url(r'^delete-association$', kanbo.hello.views.delete_association, name='hello-delete-association'),
    url(r'^logout$', kanbo.hello.views.log_out, name='hello-log-out'),
]
