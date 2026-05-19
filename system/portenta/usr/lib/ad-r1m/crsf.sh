#!/bin/bash

# Trixie uses libgpiod 2, bookworm uses libgpiod 1, `gpioset` calls are not cross compatible
GPIOSET=$(which gpioset)
if $GPIOSET -v | grep -q ' v2.'; then
	function gpioset() {
		$GPIOSET -z -t 0 -c $@
	}
fi

echo "Power cycle CRSF transceiver"
gpioset 8 2=0
sleep 0.5
gpioset 8 2=1
