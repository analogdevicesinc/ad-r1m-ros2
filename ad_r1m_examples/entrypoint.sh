#!/bin/bash
set -e

# Setup ros2 environment
if [ -f /opt/ros/humble/setup.bash ]; then
    source "/opt/ros/humble/setup.bash" --
fi

# Setup ADI ROS2 environment
if [ -f /opt/ros/adi_ros2/setup.bash ]; then
    source "/opt/ros/adi_ros2/setup.bash" --
fi

# Setup application environment
if [ -f /ros2_ws/install/setup.sh ]; then
    source "/ros2_ws/install/setup.sh" --
fi

export RMW_IMPLEMENTATION=rmw_zenoh_cpp

exec "$@"

