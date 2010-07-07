from __future__ import with_statement
from fabric.api import *

env.repo = 'git://dev.dredd.it/dreddit-auth.git'

def production():
    env.hosts = ['matalok@web1.dredd.it']
    env.path = '/home/matalok/auth'

def test():
    env.hosts = ['auth@web2.dredd.it']
    env.path = '/home/auth'

def setup():
    require('hosts')
    require('path')

    #sudo('aptitude install python-virtualenv')
    deploy_repo()

    setup_virtualenv()
    setup_db()

def push():
    require('hosts')
    require('path')

    update_repo()
    setup_virtualenv()
    migrate()

def setup_virtualenv():
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('./setup-env.sh' % env)

def setup_db():
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('cp dbsettings.py.example dbsettings.py' % env)
        run('env/bin/python manage.py syncdb --noinput --migrate')

def deploy_repo():
    require('hosts')
    require('path')

    run('mkdir -p %(path)s' % env)
    with cd(env.path):
        run('git clone %(repo)s' % env)
        
def update_repo():
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('git pull')

def migrate():
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('env/bin/python manage.py migrate')


def start():
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('./start.sh')

def stop():
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('kill `cat auth.pid`')
        run('rm -f auth.pid')

def restart()
    stop()
    start()



