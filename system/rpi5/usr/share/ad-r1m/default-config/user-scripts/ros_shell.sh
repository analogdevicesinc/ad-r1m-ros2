#!/usr/bin/env bash

xhost +
CONTAINER=$(docker run -itd --network=host --pid=host --ipc=host \
	-e DISPLAY --volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
	-e RMW_IMPLEMENTATION -v $HOME/ros_data:/ros_data \
	working)
docker attach $CONTAINER
docker commit $CONTAINER working

