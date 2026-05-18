#!/usr/bin/env bash

pushd $(dirname $0)

# === Environment variable inputs ===

# RMW_IMPLEMENTATION supported values:
#   rmw_zenoh_cpp (default)
#   rmw_fastdds_cpp
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_zenoh_cpp}

# TELEOP supported values:
#   radio (default) - ELRS remote control
#   keyboard        - SSH remote control
#   autonomous      - No user control. Armed by default. No way to disarm/e-stop.
export TELEOP=${TELEOP:-radio}

# LOCALIZATION supported values:
#   blind (default) - No true localization, just trust odometry dead reckoning based on IMU and wheel encoders
#   amcl            - Use a pre-existing map to localize the robot based on depth camera inputs using AMCL
export LOCALIZATION=${LOCALIZATION:-blind}

# NAVIGATION supported values:
#   (none by default) - No navigation, only manual inputs
#   nav2              - Start nav2 for autonomous navigation
export NAVIGATION=${NAVIGATION:-}

# ROBOT_NAMESPACE. Default value: hostname with - replaced with _. Shouldn't contain leading or trailing slashes.
default_ROBOT_NAMESPACE=$(hostname)
default_ROBOT_NAMESPACE=${default_ROBOT_NAMESPACE//-/_}
export ROBOT_NAMESPACE=${ROBOT_NAMESPACE:-$default_ROBOT_NAMESPACE}
#export ROBOT_NAMESPACE=

# ^^^ Environment variable inputs ^^^

COMPOSE_PROFILES=rmw_zenoh,rmw_fastdds,teleop_radio,teleop_autonomous,localization_blind,map_server,localization_amcl,navigation_nav2 docker compose down --remove-orphans

# Power cycle CRSF transceiver
gpioset 0 24=0
sleep 0.1
gpioset 0 24=1

# Reset all CANopen devices - sure way to halt drives and such
cansend can0 000#8100
sleep 0.1

# CAN reset
sudo ./recan.sh

# Set IMU frequency
iio_attr -u ip:localhost -d adis16470 sampling_frequency 200 >/dev/null
sudo systemctl restart iiod.service

# Prepare docker compose profiles and extra options based on passed configurations

case $RMW_IMPLEMENTATION in
rmw_zenoh_cpp)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}rmw_zenoh"
	;;

rmw_fastdds_cpp)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}rmw_fastdds"
	export ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER:-127.0.0.1:11811}
	;;
esac

case $TELEOP in
radio)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}teleop_radio"
	;;
keyboard)
	;;
autonomous)
	# Use 'docker compose run --rm teleop_autonomous' to start teleop in another terminal
	#export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}teleop_autonomous"
	;;
esac

case $LOCALIZATION in
blind)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}localization_blind"
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}map_server"
	;;
amcl)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}localization_amcl"
	;;
esac

case "$NAVIGATION" in
"")
	;;

nav2)
	export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}navigation_nav2"
	;;
esac

echo ""
echo "----------------------------------------------"
echo "Starting AD-R1M ROS 2 containers with options:"
echo "RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
echo "TELEOP=$TELEOP"
echo "LOCALIZATION=$LOCALIZATION"
echo "NAVIGATION=$NAVIGATION"
echo "ROBOT_NAMESPACE=$ROBOT_NAMESPACE"
echo "COMPOSE_PROFILES=$COMPOSE_PROFILES"
echo "----------------------------------------------"
echo ""

docker compose up --force-recreate --scale tof_republish=0
