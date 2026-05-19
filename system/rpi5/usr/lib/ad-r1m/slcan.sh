#!/bin/bash

# Trixie uses libgpiod 2, bookworm uses libgpiod 1, `gpioset` calls are not cross compatible
GPIOSET=$(which gpioset)
if $GPIOSET -v | grep -q ' v2.'; then
	function gpioset() {
		$GPIOSET -z -t 0 -c $@
	}
fi

# Reset all CANopen devices - sure way to halt drives and such
ip link | grep -q 'can0' && {
    cansend can0 000#8100
    sleep 0.1
}

# Kill daemon if already up
killall -q slcand

# Power cycle SLCAN MCU
gpioset 0 21=0
sleep 0.1
gpioset 0 21=1
sleep 0.5

# Start slcan daemon and activate interface
slcand -o -c -f -t hw -s 6 -S 2000000 /dev/ttyCAN can0
ip link set can0 up
