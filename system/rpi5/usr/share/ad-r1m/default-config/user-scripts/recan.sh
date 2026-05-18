#!/bin/bash
#
# recan: (Re)initialize CAN bus adapters
# 
# Copyright (c) 2025 Analog Devices, Inc.

# Choose adapter type:
# slcan = Use the on-board CAN adapter on the ADRD4161
# external = Use an external USB-CAN adapter
ADAPTER_TYPE=slcan

if [ $ADAPTER_TYPE == "slcan" ]; then
	sudo killall slcand

	# Power cycle SLCAN MCU. With the latest firmware, this shouldn't be necessary,
	# but while developing the SLCAN FW this was useful for when it hung.
	gpioset 0 21=0
	sleep 0.1
	gpioset 0 21=1
	sleep 0.5

	# Start slcan daemon and activate interface
	sudo slcand -o -c -f -t hw -s 6 -S 2000000 /dev/ttyCAN slcan0
	sudo ip link set slcan0 up
elif [ $ADAPTER_TYPE == "gs_usb" ]; then
	sudo ip link set can0 down
	sudo ip link set can0 type can bitrate 500000
	sudo ip link set can0 up
else
	echo "ERROR: Unknown CAN adapter type $ADAPTER_TYPE"
	exit 1
fi

