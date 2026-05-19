#!/bin/bash

# AD-R1M status LED script
# Argument  | When called?           | LED pattern
# ==========|========================|===============================
# boot      | Linux boot             | blinking 1Hz
# off       | ROS 2 off              | turn off
# on        | ROS 2 healthy          | turn on
# unhealthy | ROS 2 unhealthy        | blinking 5Hz
# [0-9A-Z]* | Arbitrary              | arbitrary morse code, then off

TIME_DIT=0.2

declare -A morse
morse[0]='- - - - -'
morse[1]='. - - - -'
morse[2]='. . - - -'
morse[3]='. . . - -'
morse[4]='. . . . -'
morse[5]='. . . . .'
morse[6]='- . . . .'
morse[7]='- - . . .'
morse[8]='- - - . .'
morse[9]='- - - - .'
morse[A]='. -'
morse[B]='- . . .'
morse[C]='- . - .'
morse[D]='- . .'
morse[E]='.'
morse[F]='. . - .'
morse[G]='- - .'
morse[H]='. . . .'
morse[I]='. .'
morse[J]='. - - -'
morse[K]='- . -'
morse[L]='. - . .'
morse[M]='- -'
morse[N]='- .'
morse[O]='- - -'
morse[P]='. - - .'
morse[Q]='- - . -'
morse[R]='. - .'
morse[S]='. . .'
morse[T]='-'
morse[U]='. . -'
morse[V]='. . . -'
morse[W]='. - -'
morse[X]='- . . -'
morse[Y]='- . - -'
morse[Z]='- - . .'

# Trixie uses libgpiod 2, bookworm uses libgpiod 1, `gpioset` calls are not cross compatible
if gpioset -v | grep -q ' v2.'; then
	function set_led() {
		gpioset -z -c 0 -t 0 22=$1
	}
else
	function set_led() {
		gpioset 0 22=$1
	}
fi

function flash_morse() {
	MSG=$1

	for (( i=0; i<${#MSG}; i++ )); do
		C=${MSG:$i:1}
		M=${morse[$C]}

		for q in $M; do
			if [ $q = '.' ]; then
				set_led 1
				sleep $TIME_DIT
				set_led 0
				sleep $TIME_DIT
			elif [ $q = '-' ]; then
				set_led 1
				sleep $TIME_DIT
				sleep $TIME_DIT
				sleep $TIME_DIT
				set_led 0
				sleep $TIME_DIT
			fi
		done

		sleep $TIME_DIT
		sleep $TIME_DIT
	done
}

function blink_hz()
{
	HALF_PERIOD=$(echo "scale=3; 1 / 2 / $1" | bc)

	# Blink until next script invocation kills this process
	while true; do
		set_led 1
		sleep $HALF_PERIOD
		set_led 0
		sleep $HALF_PERIOD
	done
}

# Kill previous invocations of this script
pkill -A $(basename $0)

case $1 in
boot)
	blink_hz 1 ;;

off)
	set_led 0 ;;

on)
	set_led 1 ;;

unhealthy)
	blink_hz 5 ;;

*)
	flash_morse "$1" ;;
esac
