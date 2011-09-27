from __future__ import with_statement
import time
import os
import os.path
from fabric.api import *
from fabric.contrib.files import *
from fabric.utils import warn
from hashlib import sha1

env.repo = 'git://dev.pleaseignore.com/dreddit-auth.git'

def production():
    "Use the production enviroment on Web1"
    env.hosts = ['dreddit@web1.pleaseignore.com']
    env.path = '/home/dreddit/apps'
    env.user = 'auth'
    env.vhost = '/auth'
    env.config = 'conf.production'
    env.uwsgiconfig = os.path.join(env.path, '..', 'etc', 'uwsgi', 'dreddit-auth.ini')
    env.password = sha1('%s-%s' % (env.user, env.vhost)).hexdigest()

    env.celeryconf = '-l INFO --settings=%(config)s --pidfile=logs/%%n.pid --logfile=logs/%%n.log -n auth.pleaseignore.com bulk default fastresponse -Q:bulk bulk -Q:fastresponse fastresponse -c 5 -c:bulk 3 -c:fastresponse 3 -B:default --scheduler=djcelery.schedulers.DatabaseScheduler' % env
    

def test():
    "Use the test enviroment on Web2"
    env.hosts = ['dreddit@web2.pleaseignore.com']
    env.path = '/home/dreddit/apps'
    env.user = 'auth'
    env.vhost = '/auth'
    env.config = 'conf.test'
    env.uwsgiconfig = os.path.join(env.path, '..', 'etc', 'uwsgi', 'dreddit-auth.ini')
    env.password = sha1('%s-%s' % (env.user, env.vhost)).hexdigest()

def deploy():
    """
    Do a fresh deployment to a new or clean server
     """
    setup()


def setup():
    """
    Deploy the files to the server and setup virtualenv and a simple
    SQlite DB setup
    """
    require('hosts')
    require('path')

    deploy_repo()

    setup_virtualenv()


def push():
    """
    Push the latest revision to the server and update the enviroment
    """
    require('hosts')
    require('path')

    stop()
    update_repo()
    setup_virtualenv()
    migrate()
    start()


def setup_virtualenv():
    """
    Generate the virtualenv enviroment
    """
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('./bin/setup-env.sh' % env)


def setup_db():
    """
    Setup a simple SQlite DB using the default settings
    """
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('env/bin/python app/manage.py syncdb --settings=%(config)s --noinput --migrate' % env)


def deploy_repo():
    """
    Do the initial repository checkout
    """
    require('hosts')
    require('path')

    run('mkdir -p %(path)s' % env)
    with cd(env.path):
        run('git clone %(repo)s' % env)

    with cd('%(path)s/dreddit-auth/' % env):
        run('mkdir logs')


def update_repo():
    """
    Pulls the latest commits to the repository
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('git pull')

    deploy_static()


def reset_repo():
    """
    Does a hard reset on the remote repo
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('git reset --hard')


def migrate():
    """
    Do any South database migrations
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('env/bin/python app/manage.py migrate --settings=%(config)s' % env)


def start_celeryd():
    """
    Start the celeryd server
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('. env/bin/activate; app/manage.py celeryd_multi start %(celeryconf)s' % env)


def stop_celeryd():
    """
    Stop any running FCGI instance
    """
    require('hosts')
    require('path')
    require('config')

    with cd('%(path)s/dreddit-auth/' % env):
        run('. env/bin/activate; app/manage.py celeryd_multi stop %(celeryconf)s' % env)


def kill_celeryd():
    """
    Kills all Celeryd instances
    """
    with cd('%(path)s/dreddit-auth/' % env):
        run("ps auxww | grep celeryd | awk '{print $2}' | xargs kill -9")

def restart_celeryd():
    """
    Restart the celery daemon
    """
    with cd('%(path)s/dreddit-auth/' % env):
        run('. env/bin/activate; app/manage.py celeryd_multi restart %(celeryconf)s' % env)

def show_celeryd():
    with cd('%(path)s/dreddit-auth/' % env):
        run('. env/bin/activate; app/manage.py celeryd_multi show %(celeryconf)s' % env)


def start_uwsgi():
    """
    Start uWSGI
    """
    pass


def restart_uwsgi():
    """
    Restart the uWSGI daemon
    """
    run('touch %(uwsgiconfig)s' % env)


def start():
    """
    Start uWSGI and Celery
    """
    start_uwsgi()
    start_celeryd()


def stop():
    """
    Stop Celery
    """
    stop_celeryd()
    info('Can\'t stop uWSGI')

def restart():
    """
    Restart uWSGI and Celery
    """
    stop_celeryd()
    time.sleep(5)
    restart_uwsgi()
    start_celeryd()

def clear_logs():
    with cd('%(path)s/dreddit-auth/' % env):
        run('rm ./logs/*.log')

def deploy_static():
    with cd('%(path)s/dreddit-auth/' % env):
        run('./app/manage.py collectstatic --settings=%(config)s -v0 --noinput' % env)

def update_permissions():
    with cd('%(path)s/dreddit-auth/' % env):
        run('./app/manage.py updatepermissions --settings=%(config)s' % env)

