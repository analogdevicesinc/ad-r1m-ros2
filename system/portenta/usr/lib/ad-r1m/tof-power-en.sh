#!/bin/bash

# Trixie uses libgpiod 2, bookworm uses libgpiod 1, `gpioset` calls are not cross compatible
GPIOSET=$(which gpioset)
if $GPIOSET -v | grep -q ' v2.'; then
	function gpioset() {
		$GPIOSET -z -t 0 -c $@
	}
fi

#x8h7_gpio 3 - BRD_RST

#MAX7322 O0 - EN_VAUX
#MAX7322 O1 - EN_VSYS
#MAX7322 I2 -
#MAX7322 I3 -
#MAX7322 I4 -
#MAX7322 I5 -
#MAX7322 O6 -
#MAX7322 O7 - F_SYNC

#EN_VSYS
gpioset 5 1=1

sleep 0.2

#EN_VAUX
gpioset 5 0=1

#ADSD3500 Reset Pin
gpioset 8 3=0

# Boot strap MAX7321
#OC0
gpioset 6 0=0

#OC1
gpioset 6 1=0

#OC2
gpioset 6 2=0

#OC3
gpioset 6 3=0

#OC4
gpioset 6 4=0

#OC5
gpioset 6 5=0

#OC6
gpioset 6 6=0

#FLASH_WP
gpioset 6 7=1

# Boot strap MAX7320
#U0 0 - INTERNAL FLASH / 1 - EXTERNAL FLASH
gpioset 7 3=0

#EN_1P8
gpioset 7 6=1

sleep 1

#EN_0P8
gpioset 7 7=1

#ADSD3500 Reset Pin
# Pull reset high
gpioset 8 3=1
