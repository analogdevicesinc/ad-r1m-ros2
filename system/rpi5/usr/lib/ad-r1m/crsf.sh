#!/bin/bash

# Trixie uses libgpiod 2, bookworm uses libgpiod 1, `gpioset` calls are not cross compatible
GPIOSET=$(which gpioset)
if $GPIOSET -v | grep -q ' v2.'; then
	function gpioset() {
		$GPIOSET -z -t 0 -c $@
	}
fi
  
# Power cycle CRSF transceiver
gpioset 0 24=0
sleep 0.1
gpioset 0 24=1
