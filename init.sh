#!/bin/sh

svn co http://code.djangoproject.com/svn/django/branches/releases/1.1.X/django django
svn co http://django-evolution.googlecode.com/svn/trunk/django_evolution
hg clone http://bitbucket.org/jespern/django-piston/
mv django-piston/piston ./
rm -rf django-piston
git clone http://github.com/bradjasper/django-jsonfield.git djang_jsonfield
