#!/bin/sh

. ./env/bin/activate
python ./manage.py runfcgi method=threaded host=127.0.0.1 port=9981
