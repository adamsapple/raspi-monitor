#!/usr/bin/sh

EXEC_FILE="7735.py"
SERVICE_FILE="pimonitor.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_FILE"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

sed -i "s|^WorkingDirectory =.*|WorkingDirectory = ${SCRIPT_DIR}|" "${SERVICE_FILE}"
sed -i "s|^ExecStart =.*|ExecStart = ${SCRIPT_DIR}/.venv/bin/python ${SCRIPT_DIR}/${EXEC_FILE}|" "${SERVICE_FILE}"

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
