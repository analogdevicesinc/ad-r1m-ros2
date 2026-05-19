FROM astanea/adi_ros2:humble-arm64-full AS ros_app

ENV DEBIAN_FRONTEND=noninteractive

# Install build & runtime tools
RUN --mount=type=cache,target=/var/cache/apt \
        apt-get update && apt-get install -y \
        python3-pip \
        ros-humble-rmw-zenoh-cpp \
        ros-humble-rqt-graph \
        ros-humble-rqt-image-view \
        ros-humble-rviz2 \
        ros-humble-ros2-control \
        && rm -rf /var/lib/apt/lists/*

# Clone ros2_ws repos, apply patches
RUN mkdir -p /ros2_ws/src
WORKDIR /ros2_ws
COPY ./entrypoint.sh .
COPY . src/ad_r1m_examples

# Install rosdep dependencies
RUN --mount=type=cache,target=/var/cache/apt \
        . /opt/ros/adi_ros2/setup.sh && \
        apt-get update && \
        rosdep update --rosdistro humble && \
        rosdep install -y --from-paths src --ignore-src && \
        rm -rf /var/lib/apt/lists/*

# Build ROS 2 nodes and clean up
RUN . /opt/ros/adi_ros2/setup.sh && \
        MAKEFLAGS="-j4" colcon build --merge-install --executor sequential && \
        rm -rf build log core

ENV DEBIAN_FRONTEND=

ENTRYPOINT ["/ros2_ws/entrypoint.sh"]
CMD ["bash"]

