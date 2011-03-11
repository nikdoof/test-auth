from __future__ import with_statement
import time
import os
from fabric.api import *
from fabric.contrib.files import *
from fabric.utils import warn
from hashlib import sha1

env.repo = 'git://dev.dredd.it/dreddit-auth.git'


def production():
    "Use the production enviroment on Web1"
    env.hosts = ['dreddit@web1.pleaseignore.com']
    env.path = '/home/dreddit/apps'
    env.user = 'auth'
    env.vhost = '/auth'
    env.password = sha1('%s-%s' % (env.user, env.vhost)).hexdigest()

def test():
    "Use the test enviroment on Web2"
    env.hosts = ['dreddit@web2.pleaseignore.com']
    env.path = '/home/dreddit/apps'
    env.user = 'auth'
    env.vhost = '/auth'
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
        run('if [ ! -e dbsettings.py ]; then cp dbsettings.py.example dbsettings.py; fi' % env)
        run('env/bin/python app/manage.py syncdb --noinput --migrate')


def generate_brokersettings():
    """
    Generates the brokersettings file
    """

    require('hosts')

    cnf = open('brokersettings.py.example', 'r').read()
    out = open('brokersettings.py', 'w')
    out.write(cnf % env)


def setup_rabbitmq():
    """
    Setup the RabbitMQ instance on the system (requires sudo access)
    """

    require('hosts')
    require('path')

    generate_brokersettings() 

    with settings(warn_only=True):
        sudo('rabbitmqctl delete_user %s' % env.user, shell=False)
        sudo('rabbitmqctl delete_vhost %s' % env.vhost, shell=False)
    sudo('rabbitmqctl add_user %s %s' % (env.user, env.password), shell=False)
    sudo('rabbitmqctl add_vhost %s' % env.vhost, shell=False)
    sudo('rabbitmqctl set_permissions -p %s %s ".*" ".*" ".*"' % (env.vhost, env.user), shell=False)

    put('./brokersettings.py', '%(path)s/dreddit-auth/app/conf/' % env)
    os.unlink('brokersettings.py')


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
        run('env/bin/python app/manage.py migrate')


def start_celeryd():
    """
    Start the celeryd server
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('. env/bin/activate; app/manage.py celeryd_detach -l INFO -B --pidfile logs/celeryd.pid -f logs/celeryd.log -n auth-processor' % env)


def stop_celeryd():
    """
    Stop any running FCGI instance
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        if exists('logs/celeryd.pid'):
            run('kill `cat logs/celeryd.pid`')
        else:
            warn('celeryd isn\'t running')

def restart_celeryd():
    """
    Restart the celery daemon
    """
    stop_celeryd()
    time.sleep(2)
    start_celeryd()


def start_uwsgi():
    with cd('%(path)s/dreddit-auth/' % env):
        run('uwsgi -d logs/uwsgi.log -x etc/auth_uwsgi.xml' % env)


def stop_uwsgi():
    with cd('%(path)s/dreddit-auth/' % env):
        if exists('logs/uwsgi.pid'):
            run('kill `cat logs/uwsgi.pid`')
        else:
            warn('uWSGI isn\'t running')


def restart_uwsgi():
    stop_uwsgi()
    time.sleep(0.5)
    start_uwsgi()


def start():
    start_uwsgi()
    start_celeryd()


def stop():
    stop_celeryd()
    stop_uwsgi()


def restart():
    stop()
    time.sleep(5)
    start()
