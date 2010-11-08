#!/bin/bash

ROOT=`pwd`
PIDFILE=$ROOT/logs/auth.pid

mkdir logs 2> /dev/null

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE` 2> /dev/null
    rm -f -- $PIDFILE
fi

sleep 1
cd $ROOT
source ./env/bin/activate
./manage.py runfcgi daemonize=true pidfile=$PIDFILE host=127.0.0.1 port=9981 errlog=$ROOT/logs/stderr.log outlog=$ROOT/logs/stdout.log
./manage.py celeryd -B > $ROOT/logs/celeryd.lg 2>&1 &
