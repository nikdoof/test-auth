from __future__ import with_statement
from fabric.api import *

env.repo = 'git://dev.dredd.it/dreddit-auth.git'

def production():
    "Use the production enviroment on Web1"
    env.hosts = ['matalok@web1.dredd.it']
    env.path = '/home/matalok'

def test():
    "Use the test enviroment on Web2"
    env.hosts = ['auth@web2.dredd.it']
    env.path = '/home/auth'

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

    #sudo('aptitude install python-virtualenv')
    deploy_repo()

    setup_virtualenv()
    setup_db()

def push():
    """
    Push the latest revision to the server and update the enviroment
    """
    require('hosts')
    require('path')

    update_repo()
    setup_virtualenv()
    migrate()

def setup_virtualenv():
    """
    Generate the virtualenv enviroment
    """
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('./setup-env.sh' % env)

def setup_db():
    """
    Setup a simple SQlite DB using the default settings
    """
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('if [ ! -e dbsettings.py ]; then cp dbsettings.py.example dbsettings.py; fi' % env)
        run('env/bin/python manage.py syncdb --noinput --migrate')

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

def migrate():
    """
    Do any South database migrations
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('env/bin/python manage.py migrate')


def start():
    """
    Start the FastCGI server
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('screen -d -m "./start.sh"')

def stop():
    """
    Stop any running FCGI instance
    """
    require('hosts')
    require('path')

    with cd('%(path)s/dreddit-auth/' % env):
        run('kill `cat auth.pid`')
        run('rm -f auth.pid')

def restart():
    """
    Restart the FCGI server
    """
    stop()
    start()



