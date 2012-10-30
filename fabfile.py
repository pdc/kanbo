# -*-coding: UTF-8 -*-
# Run these commands with fab

from fabric.api import local, settings, abort, run, cd, env, sudo
from fabric.contrib.console import confirm

env.hosts = ['kanbo@spreadsite.org']
env.site_name = 'kanbo'
env.virtualenv = env.site_name
env.django_apps = ['board', 'about', 'hello']

def update_requirements():
    local("pip freeze | egrep -v 'Fabric|pycrypto|ssh' > REQUIREMENTS")

def virtualenv(command, user=None):
    run('. /home/{0}/virtualenvs/{1}/bin/activate && {2}'.format(env.site_name, env.virtualenv, command))

def test():
    with settings(warn_only=True):
        result = local('./manage.py test {0}'.format(' '.join(env.django_apps)), capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")

def push():
    local('git push')

def deploy():
    test()
    push()

    code_dir = '/home/{0}/Sites/{0}'.format(env.site_name)
    with cd(code_dir):
        run('git pull')
        virtualenv('./manage.py collectstatic --noinput')

    ##run('svc -du /service/{0}'.format(env.site_name))