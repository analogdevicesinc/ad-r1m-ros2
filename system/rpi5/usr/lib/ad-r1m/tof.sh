#!/bin/bash

# Restart ToF software
ping -c2 -w2 192.168.56.1 && {
	echo "Restarting ToF software"
	echo analog | sshpass -panalog ssh analog@192.168.56.1 "sudo -S systemctl restart ros2-docker-app.service"
} || {
	echo "Couldn't reach ToF camera"
}
