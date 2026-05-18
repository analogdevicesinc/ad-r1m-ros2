#!/usr/bin/env bash

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

# ROBOT_NAMESPACE. Default value: hostname with - replaced with _. Shouldn't start with a "/".
default_ROBOT_NAMESPACE=$(hostname)
default_ROBOT_NAMESPACE=${default_ROBOT_NAMESPACE//-/_}
export ROBOT_NAMESPACE=${ROBOT_NAMESPACE:-$default_ROBOT_NAMESPACE}
# export ROBOT_NAMESPACE=  # uncomment to disable namespace for mapping

# ^^^ Environment variable inputs ^^^
pushd $(dirname $0)
COMPOSE_PROFILES="rmw_zenoh,rmw_fastdds,teleop_radio,teleop_autonomous,mapping,localization_blind,localization_amcl,navigation_nav2" docker compose down --remove-orphans

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
esac

export COMPOSE_PROFILES="${COMPOSE_PROFILES}${COMPOSE_PROFILES:+,}mapping"

echo ""
echo "----------------------------------------------"
echo "Starting AD-R1M ROS 2 containers with options:"
echo "RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
echo "TELEOP=$TELEOP"
echo "ROBOT_NAMESPACE=$ROBOT_NAMESPACE"
echo "COMPOSE_PROFILES=$COMPOSE_PROFILES"
echo "----------------------------------------------"
echo ""

docker compose up --force-recreate
