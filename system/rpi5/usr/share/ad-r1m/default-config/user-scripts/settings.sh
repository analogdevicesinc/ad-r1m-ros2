#!/usr/bin/env bash

SCRIPT_DIR=$(readlink -f $(dirname $0))

options[1]="Change hostname"
options[2]="Connect to WiFi"
options[3]="Download latest docker image"
options[4]="Write CAN adapter firmware"
options[5]="Write default motor tuning"
options[6]="Bind radio receiver"
options[7]="Exit"

next_recommended="Change hostname"

while true; do
	opt=$(gum choose --header="Settings:" --selected="$next_recommended" "${options[@]}")

	case $opt in
		"Change hostname")
			hostname=$(gum input --header="Hostname:" --value=$(hostname))
		       	
			if [ $? != 0 ] || [ -z "$hostname" ] || [ "$(hostname)" == "$hostname" ]; then continue; fi

			gum log -sl info "Changing hostname to \"$hostname\""
			echo $hostname | sudo sed -i "s/$(hostname)/$hostname/g" /etc/hosts /etc/hostname
			sudo hostname $hostname

			next_recommended="Connect to WiFi"
			;;
		"Connect to WiFi")
			gum log -sl info "Opening nmtui for WiFi configuration"

			sudo nmtui

			next_recommended="Download latest docker image"
			;;
		"Download latest docker image")
			gum log -sl info "Downloading latest docker image"

			docker login docker.cloudsmith.io
			$SCRIPT_DIR/recreate_container.sh

			next_recommended="Write CAN adapter firmware"
			;;
		"Write CAN adapter firmware")
			gum log -sl info "Writing CAN adapter firmware"

			/opt/adrd4161-fw/upload.sh /opt/adrd4161-fw/adrd4161_slcan.elf

			sudo $SCRIPT_DIR/recan.sh

			next_recommended="Write default motor tuning"
			;;
		"Write default motor tuning")
			cansend slcan0 000#8114
			gum spin --title "Waiting for left drive heartbeat (714)" -- bash -c "candump slcan0 | timeout 1 grep -q 714"
			gum log -sl info "Writing default motor tuning to left drive"
			/opt/adrd3161/param_tool.sh -i slcan0 -e /opt/adrd3161/adrd3161.eds 0x14 write /opt/adrd3161/qsh5718_basic.ini

			cansend slcan0 000#8116
			gum spin --title "Waiting for right drive heartbeat (716)" -- bash -c "candump slcan0 | timeout 1 grep -q 716"
			gum log -sl info "Writing default motor tuning to right drive"
			/opt/adrd3161/param_tool.sh -i slcan0 -e /opt/adrd3161/adrd3161.eds 0x16 write /opt/adrd3161/qsh5718_basic.ini

			next_recommended="Bind radio receiver"
			;;
		"Bind radio receiver")

			gum spin --title "Power cycling receiver 3 times" -- bash -c "gpioset 0 24=0; sleep 1
				gpioset 0 24=1; sleep 2; gpioset 0 24=0; sleep 0.5
				gpioset 0 24=1; sleep 2; gpioset 0 24=0; sleep 0.5
				gpioset 0 24=1; sleep 2; gpioset 0 24=0; sleep 0.5
				gpioset 0 24=1"

			gum log -sl info "Power cycled radio received. It should be in bind mode and double-blinking."
			gum log -sl info "  On your RC handset:"
			gum log -sl info "    1. Go to the main screen (press RET a few times)"
			gum log -sl info "    2. Navigate to SYS > ExpressLRS"
			gum log -sl info "    3. Press the [Bind] menu button"
			gum log -sl info " "
			gum log -sl info "  After that, the transceiver should stop double-blinking and show a solid color."

			next_recommended="Exit"
			;;
		"Exit"|*)
			break
			;;
	esac
done

gum log -sl info "Goodbye!"

