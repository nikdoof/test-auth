#!/bin/bash

PIDFILE='auth.pid'

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

sleep 1
source ./env/bin/activate
./manage.py runfcgi daemonize=false pidfile=$PIDFILE host=127.0.0.1 port=9981 &
exit 0
