from __future__ import with_statement
import time
import os
import os.path
from fabric.api import cd, run, require, prefix, env, task, local
from fabric.contrib.files import exists
from fabric.utils import warn
from hashlib import sha1

env.shell = '/bin/bash -l -c'
env.workers = []
env.repo = 'git://dev.pleaseignore.com/dreddit-auth.git'

@task(alias='prod')
def production():
    """Use the production enviroment on Web1"""
    env.hosts = ['dreddit@web1.pleaseignore.com']
    env.path = '/home/dreddit/apps/dreddit-auth'
    env.config = 'conf.production'
    env.uwsgiconfig = os.path.join(env.path, '..', '..', 'etc', 'uwsgi', 'dreddit-auth.ini')
    env.celeryconf = '-l INFO --settings=%(config)s --pidfile=logs/%%n.pid --logfile=logs/%%n.log -n auth.pleaseignore.com bulk default fastresponse -Q:bulk bulk -Q:fastresponse fastresponse -c 5 -c:bulk 3 -c:fastresponse 3 -B:default --scheduler=djcelery.schedulers.DatabaseScheduler' % env

    
@task
def test():
    """Use the test enviroment on Web2"""
    env.hosts = ['dreddit@web2.pleaseignore.com']
    env.path = '/home/dreddit/apps/dreddit-auth'
    env.config = 'conf.test'
    env.uwsgiconfig = os.path.join(env.path, '..', 'etc', 'uwsgi', 'dreddit-auth.ini')
    

@task
def deploy(tag=None):
    """Deploy current HEAD in "master", or a tag is provided"""
    require('hosts')
    require('path')

    git_update_repo(tag)
    setup_virtualenv()
    sync_db()
    deploy_static()


@task
def restart():
    """Restart UWSGI and Celeryd"""
    restart_uwsgi()
    clear_logs()
    restart_celeryd()


@task(alias='update')
def git_update_repo(tag):
    """Update the server's repo from master"""
    with cd('%(path)s' % env):
        run('git reset --hard')
        run('git fetch --all')
        if tag:
            run('git checkout %s' % tag)
        else:
            run('git checkout master')
            

@task(alias='virtualenv')
def setup_virtualenv():
    """Sets up and updates the virtualenv install"""
    require('path')
    with cd('%(path)s' % env):
        if not exists('.env'):
            run('virtualenv --no-site-packages .env')
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('pip install -r requirements.txt')


@task(alias='dbsync')
def sync_db():
    """Syncs the DB and completes any migrations"""
    require('hosts')
    require('path')

    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            #run('app/manage.py syncdb --settings=%(config)s' % env)
            update_permissions()
            run('app/manage.py migrate --settings=%(config)s' % env)


@task(alias='static')
def deploy_static():
    """Deploys the static files to the defined location"""
    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py collectstatic --settings=%(config)s -v0 --noinput' % env)


@task
def clear_logs():
    """Clears any old celeryd logs"""
    with cd('%(path)s' % env):
        run('rm ./logs/*.log')


@task
def update_permissions():
    """Updates permissions that syncdb would of missed"""
    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py updatepermissions --settings=%(config)s' % env)


@task
def start_celeryd():
    """Start the celeryd server"""
    require('hosts')
    require('path')

    clear_logs()
    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py celeryd_multi start %(celeryconf)s' % env)

@task
def stop_celeryd():
    """Stop the celeryd server"""
    require('hosts')
    require('path')
    require('config')

    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py celeryd_multi stop %(celeryconf)s' % env)


@task
def restart_celeryd():
    """Restart the celery daemon"""
    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py celeryd_multi restart %(celeryconf)s' % env)


@task
def show_celeryd():
    with cd('%(path)s' % env):
        with prefix('source %(path)s/.env/bin/activate' % env):
            run('app/manage.py celeryd_multi show %(celeryconf)s' % env)


@task
def restart_uwsgi():
    """
    Restart the uWSGI daemon
    """
    run('touch %(uwsgiconfig)s' % env)

###### Local Tasks

@task
def runserver(port=3333):
    with prefix('. .env/bin/activate'):
        local('app/manage.py runserver %s' % port, capture=False)

@task
def test():
    with prefix('. .env/bin/activate'):
        local('app/manage.py test --noinput --failfast')


