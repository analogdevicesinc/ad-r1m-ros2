FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

# Add OSRF Gazebo repository for Gazebo Harmonic packages
RUN apt-get update && apt-get install -y wget lsb-release gnupg && \
    wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
      > /etc/apt/sources.list.d/gazebo-stable.list && \
    rm -rf /var/lib/apt/lists/*

# Install Gazebo Harmonic + ROS bridge + HIL demo dependencies
# NOTE: ros-humble-gz-ros2-control is NOT installed from apt -- it links
# against Fortress (gz-sim6). We build it from source below for Harmonic.
RUN apt-get update && apt-get install -y \
    ros-humble-ros-gzharmonic \
    ros-humble-imu-filter-madgwick \
    ros-humble-robot-localization \
    ros-humble-twist-mux \
    ros-humble-controller-manager \
    ros-humble-diff-drive-controller \
    ros-humble-joint-state-broadcaster \
    ros-humble-robot-state-publisher \
    ros-humble-tf-transformations \
    ros-humble-rviz2 \
    ros-humble-xacro \
    python3-pip \
    git \
    xterm \
    && rm -rf /var/lib/apt/lists/*

# Build gz_ros2_control from source against Harmonic (gz-sim8)
# Only the core plugin packages -- demos have deps unavailable on Humble.
ENV GZ_VERSION=harmonic
RUN mkdir -p /opt/gz_ros2_control_ws/src && \
    cd /opt/gz_ros2_control_ws/src && \
    git clone -b humble https://github.com/ros-controls/gz_ros2_control.git && \
    rm -rf gz_ros2_control/gz_ros2_control_demos && \
    cd /opt/gz_ros2_control_ws && \
    . /opt/ros/humble/setup.sh && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y \
        --skip-keys="gz-sim8 gz-plugin2 gz_ros2_control_demos" && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release && \
    rm -rf build log src

RUN mkdir -p /ros2_ws/src
WORKDIR /ros2_ws

COPY entrypoint.sh /ros2_ws/entrypoint.sh

ENV DEBIAN_FRONTEND=

ENTRYPOINT ["/ros2_ws/entrypoint.sh"]
CMD ["bash"]
