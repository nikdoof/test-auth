#!/bin/sh

/usr/bin/python ./manage.py runfcgi method=threaded host=127.0.0.1 port=9981
