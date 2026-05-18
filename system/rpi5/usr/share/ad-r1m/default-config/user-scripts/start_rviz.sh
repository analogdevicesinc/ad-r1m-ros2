#!/usr/bin/env bash

xhost +
docker run -it --rm --network=host --pid=host --ipc=host \
	-e DISPLAY -v "$HOME/.Xauthority:/root/.Xauthority:rw" \
	-e RMW_IMPLEMENTATION -v "$HOME/ros_data:/ros_data" \
working rviz2 -d /ros2_ws/install/ad_r1m_description/share/ad_r1m_description/rviz/main.rviz

