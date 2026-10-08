#!/bin/bash
set -e

# Setup ROS 2 environment
if [ -f /opt/ros/humble/setup.bash ]; then
    source "/opt/ros/humble/setup.bash" --
fi

# Source gz_ros2_control built from source (Harmonic underlay)
if [ -f /opt/gz_ros2_control_ws/install/setup.bash ]; then
    source "/opt/gz_ros2_control_ws/install/setup.bash" --
fi

# Setup application environment
if [ -f /ros2_ws/install/setup.sh ]; then
    source "/ros2_ws/install/setup.sh" --
fi

exec "$@"
