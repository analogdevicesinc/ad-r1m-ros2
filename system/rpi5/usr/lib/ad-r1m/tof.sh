#!/bin/bash

# Restart ToF software
ping -c2 -w2 192.168.56.1 && {
	echo "ToF: Synchronizing clock"
	echo analog | sshpass -panalog ssh analog@192.168.56.1 "sudo -S chronyc makestep"
	echo analog | sshpass -panalog ssh analog@192.168.56.1 "sudo -S chronyc burst 4/8 192.168.56.10"
	echo "ToF: Restarting ROS 2 node"
	echo analog | sshpass -panalog ssh analog@192.168.56.1 "sudo -S systemctl restart ros2-docker-app.service"
} || {
	echo "Couldn't reach ToF camera"
}
