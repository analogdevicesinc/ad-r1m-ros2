AD-R1M ROS 2 Getting Started
============================

This guide covers setting up ROS 2 on your development PC to communicate with and visualize the AD-R1M robot.

.. contents:: Table of Contents
   :depth: 2
   :local:

.. _ros2-host-installation:

Host PC ROS 2 Installation
--------------------------

Install ROS 2 Humble on Ubuntu 22.04 following the `official installation guide <https://docs.ros.org/en/humble/Installation.html>`__.

Set Locale
~~~~~~~~~~

.. code-block:: bash

   locale  # check for UTF-8

   sudo apt update && sudo apt install locales
   sudo locale-gen en_US en_US.UTF-8
   sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
   export LANG=en_US.UTF-8

   locale  # verify settings

Setup Sources
~~~~~~~~~~~~~

.. code-block:: bash

   # Enable Ubuntu Universe repository
   sudo apt install software-properties-common
   sudo add-apt-repository universe

   # Add ROS 2 apt repository
   sudo apt update && sudo apt install curl -y
   export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
   curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
   sudo dpkg -i /tmp/ros2-apt-source.deb

Install ROS 2 Humble
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update apt cache
   sudo apt update
   sudo apt upgrade

   # Install ROS 2 Humble Desktop (includes RViz, demos, tutorials)
   sudo apt install -y ros-humble-desktop

   # Source ROS 2
   echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
   source ~/.bashrc

.. warning::

   Run ``sudo apt upgrade`` before installing ROS 2 to ensure systemd and udev-related packages are updated.

Install Zenoh RMW
~~~~~~~~~~~~~~~~~

The AD-R1M uses Zenoh middleware for ROS 2 communication. Install the Zenoh RMW implementation:

.. code-block:: bash

   sudo apt update
   sudo apt install ros-humble-rmw-zenoh-cpp

See `rmw_zenoh documentation <https://github.com/ros2/rmw_zenoh>`__ for more details.

Install Additional Tools (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Visualization and debugging tools
   sudo apt install -y ros-humble-rviz2 ros-humble-rqt ros-humble-rqt-common-plugins

   # TF debugging
   sudo apt install -y ros-humble-tf2-tools

   # Nav2 tools (for visualization)
   sudo apt install -y ros-humble-nav2-rviz-plugins

.. _ros2-communication:

Communicating with the Robot
----------------------------

The AD-R1M uses Zenoh middleware for efficient, multi-robot ROS 2 communication.

Configure Zenoh Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~

Set environment variables to connect to the robot:

.. code-block:: bash

   # Set RMW implementation to Zenoh
   export RMW_IMPLEMENTATION=rmw_zenoh_cpp
   
   # Configure Zenoh to connect to robot (replace with actual IP)
   export ROBOT_IP=<robot-ip-address>
   export ZENOH_CONFIG_OVERRIDE='connect/endpoints=["tcp/${ROBOT_IP}:7447"];mode="client"'

Verify Connection
~~~~~~~~~~~~~~~~~

Once configured, verify ROS 2 can see robot topics:

.. code-block:: bash

   # List available topics
   ros2 topic list

You should see topics like:

- ``/imu`` - IMU sensor data
- ``/odom`` - Robot odometry
- ``/cam1/scan`` - Laser scan from ToF camera
- ``/cmd_vel`` - Velocity commands

.. code-block:: bash

   # Echo sensor data
   ros2 topic echo /imu --once

   # Check topic frequency
   ros2 topic hz /imu

Alternative: Fast-DDS with Discovery Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If using Fast-DDS instead of Zenoh:

.. code-block:: bash

   export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
   export ROS_DISCOVERY_SERVER=${ROBOT_IP}:11811
   ros2 topic list

.. _ros2-visualization:

RViz Visualization
------------------

Using start_rviz.sh Script
~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to launch RViz is using the provided script:

.. code-block:: bash

   # Navigate to the scripts directory
   cd platform/common/scripts

   # Start RViz for robot 0 (with namespace)
   ./start_rviz.sh 0

   # Single robot mode (no namespace)
   ./start_rviz.sh 0 false

**What the script does:**

- Configures Zenoh to connect to ``ad-r1m-<N>.local``
- Sets up RViz with correct namespace and topic remappings
- Loads pre-configured RViz layout from ``ad_r1m_base/rviz/main.rviz``
- Enables interactive tools (2D Pose Estimate, 2D Nav Goal)

Manual RViz Launch
~~~~~~~~~~~~~~~~~~

For custom configurations:

.. code-block:: bash

   # Set environment (replace IP)
   export RMW_IMPLEMENTATION=rmw_zenoh_cpp
   export ROBOT_IP=192.168.1.100
   export ZENOH_CONFIG_OVERRIDE='connect/endpoints=["tcp/${ROBOT_IP}:7447"];mode="client"'

   # Launch RViz
   ros2 run rviz2 rviz2

Then add displays manually:

- **RobotModel**: Set to ``/robot_description``
- **TF**: Enable to see transform tree
- **LaserScan**: Set topic to ``/cam1/scan``
- **Map**: Set topic to ``/map`` (when mapping or navigating)

.. _ros2-tips:

Tips and Best Practices
-----------------------

Multi-Robot Setup
~~~~~~~~~~~~~~~~~

When working with multiple robots, each robot uses a namespace (e.g., ``ad_r1m_0``, ``ad_r1m_1``):

.. code-block:: bash

   # View topics for specific robot
   ros2 topic list | grep ad_r1m_0
   
   # Echo namespaced topic
   ros2 topic echo /ad_r1m_0/imu

   # Start RViz for robot 1
   ./start_rviz.sh 1

Useful ROS 2 Commands
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all nodes
   ros2 node list

   # Get info about a node
   ros2 node info /motors/controller_manager

   # List topics with types
   ros2 topic list -t

   # Record topics to bag file
   ros2 bag record /imu /odom /cam1/scan -o sensor_data

   # Play back recorded data
   ros2 bag play sensor_data

   # View TF tree (generates PDF)
   ros2 run tf2_tools view_frames

Debugging Communication
~~~~~~~~~~~~~~~~~~~~~~~

If topics are not visible:

1. **Check Zenoh router is running on robot**:

   .. code-block:: bash

      ssh analog@ad-r1m-0.local
      docker compose ps | grep zenoh

2. **Verify network connectivity**:

   .. code-block:: bash

      ping ad-r1m-0.local

3. **Check RMW configuration**:

   .. code-block:: bash

      echo $RMW_IMPLEMENTATION
      echo $ZENOH_CONFIG_OVERRIDE

4. **Try direct IP instead of hostname**:

   .. code-block:: bash

      export ROBOT_IP=192.168.1.100  # Use actual IP

For more troubleshooting, see :doc:`/how-to/troubleshooting`.

Common Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~~

Add to your ``~/.bashrc`` for convenience:

.. code-block:: bash

   # ROS 2 setup
   source /opt/ros/humble/setup.bash
   
   # Function to connect to AD-R1M robot
   connect_robot() {
       local robot_num=${1:-0}
       export RMW_IMPLEMENTATION=rmw_zenoh_cpp
       export ROBOT_IP="ad-r1m-${robot_num}.local"
       export ZENOH_CONFIG_OVERRIDE='connect/endpoints=["tcp/${ROBOT_IP}:7447"];mode="client"'
       echo "Connected to ad-r1m-${robot_num}"
   }

Usage:

.. code-block:: bash

   connect_robot 0    # Connect to ad-r1m-0
   ros2 topic list    # View robot topics
