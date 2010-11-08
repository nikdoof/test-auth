#!/bin/bash

ROOT=`pwd`
PIDROOT=$ROOT/logs

AUTH_PID_FILE="$PIDROOT/auth.pid"
CELERYD_PID_FILE="$PIDROOT/celeryd.pid"

mkdir logs 2> /dev/null

if [ -f $AUTH_PID_FILE ]; then
    kill `cat -- $AUTH_PID_FILE` 2> /dev/null
    rm -f -- $AUTH_PID_FILE
fi

if [ -f $CELERYD_PID_FILE ]; then
    kill `cat -- $CELERYD_PID_FILE` 2> /dev/null
    rm -f -- $CELERYD_PID_FILE
fi


sleep 1
cd $ROOT
source ./env/bin/activate

./manage.py celeryd -B -E -l INFO --pidfile $CELERYD_PID_FILE > $ROOT/logs/celeryd.log 2>&1 &
./manage.py runfcgi daemonize=true pidfile=$AUTH_PID_FILE host=127.0.0.1 port=9981 errlog=$ROOT/logs/stderr.log outlog=$ROOT/logs/stdout.log
