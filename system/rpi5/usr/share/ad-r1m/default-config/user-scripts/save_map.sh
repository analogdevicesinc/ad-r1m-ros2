#!/bin/bash

MAP_NAME=map
docker run -it --rm --network=host --pid=host --ipc=host \
	-e RMW_IMPLEMENTATION -v "$HOME/ros_data:/ros_data" \
	working ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name:{ data: '/ros_data/maps/$MAP_NAME'}}"

