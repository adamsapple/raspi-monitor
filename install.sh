#!/usr/bin/sh

EXEC_FILE="7735.py"
SERVICE_FILE="pimonitor.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_FILE"

# echo $SERVICE_FILE_PATH

if [ ! -e $SERVICE_FILE_PATH ]; then
    cp $SERVICE_FILE $SERVICE_FILE_PATH
else
    echo $SERVICE_FILE is already exist.
fi

chmod 755 $EXEC_FILE

# sudo systemctl daemon-reload

echo enable service
systemctl enable $SERVICE_FILE

echo start service
systemctl start $SERVICE_FILE

echo $SERVICE_FILE install finished.
