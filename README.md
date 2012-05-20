TEST Auth
=========

TEST Auth is a central access management system for EVE Online corporations and alliances, it stores and manages EVE API keys and assigns access permissions based on defined permissions.

Included is a HR management system, a group management system and a basic API key viewer showing Character and skill information.


Requirements
------------

The requirements.txt covers all dependencies for Auth, setup a virtual env and install the requirements:

virtualenv env
. env/bin/activate
pip install -r requirements.txt

As we're using system wide packages, its advisable to install python-mysql packages system wide, otherwise you'll need a basic build env on your machine (build-essentials, python-dev on Debian).

Bootstrap
---------

Auth uses Twitter Bootstrap v1 for its design layout, its yet to be updated to v2.0. You can grab the older version from the URL below, extract it into app/sso/static/bootstrap/

https://github.com/twitter/bootstrap/tarball/v1.4.0

Running
-------

For dev, use ./manage.py runserver <ip>:<port>, after loading the virtualenv. In development Celery will operate in-process and doesn't require a seperate celeryd process to execute.

For Live instances its advisable to run within a WSGI container server such as uWSGI. 

