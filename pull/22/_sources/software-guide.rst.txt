AD-R1M Software Guide
=====================

This guide covers software installation, configuration, and operation for the AD-R1M Open Mobile Robot Platform.

.. contents:: Table of Contents
   :depth: 2
   :local:

Overview
--------

The AD-R1M software stack is built on **ROS 2 Humble** running on ADI Kuiper2 Linux. The architecture includes:

- **ROS 2 Nodes** for motor control, sensor integration, localization, and navigation
- **ros2_control** framework for hardware abstraction
- **Nav2** navigation stack for autonomous operation
- **Docker containers** for isolated, reproducible deployments

Software Downloads
------------------

AD-R1M Software Package
~~~~~~~~~~~~~~~~~~~~~~~

The AD-R1M ROS 2 packages are available on GitHub:

- `ad-r1m-ros2 <https://github.com/analogdevicesinc/ad-r1m-ros2>`__

Prerequisites
~~~~~~~~~~~~~

**On the Robot (Raspberry Pi 5):**

- ADI Kuiper2 Linux (pre-installed on SD card)
- ROS 2 Humble (pre-installed)
- Docker and Docker Compose (pre-installed)

**On the Host PC (for development/visualization):**

- Ubuntu 22.04 LTS
- ROS 2 Humble Desktop
- RViz2 for visualization

For host PC setup instructions, see :ref:`ros2-host-installation`.

Installation
------------

.. _sd-card-setup:

SD Card Setup
~~~~~~~~~~~~~

For instructions on setting up the SD card and installing the AD-R1M system software, see :doc:`how-to/build-from-scratch/setup-rpi`.

.. _first-boot-configuration:

First Boot Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

The AD-R1M includes an interactive setup script to configure the robot on first boot.

1. Connect a monitor and keyboard to the Raspberry Pi (or use serial console)

2. Login with default credentials:

   - Username: ``analog``
   - Password: ``analog``

3. Run the interactive setup script:

   .. code-block:: bash

      ~/setup.sh

   The script provides a menu-driven interface:

   .. code-block:: text

      ╔════════════════════════════════════════════════════════════════╗
      ║              AD-R1M First Boot Setup Menu                      ║
      ╠════════════════════════════════════════════════════════════════╣
      ║  1) Change hostname                                            ║
      ║     Set a unique hostname for the robot                        ║
      ║     (recommended for multi-robot setups)                       ║
      ║                                                                ║
      ║  2) Connect to WiFi                                            ║
      ║     Opens nmtui for network configuration                      ║
      ║                                                                ║
      ║  3) Download latest docker image                               ║
      ║     Pulls the latest AD-R1M container from Cloudsmith          ║
      ║                                                                ║
      ║  4) Write CAN adapter firmware                                 ║
      ║     Uploads firmware to the ADRD4161 CAN adapter board         ║
      ║                                                                ║
      ║  5) Write default motor tuning                                 ║
      ║     Writes PID parameters to motor controllers (ADRD3161)      ║
      ║                                                                ║
      ║  6) Bind radio receiver                                        ║
      ║     Puts the ELRS receiver into bind mode                      ║
      ║                                                                ║
      ║  0) Exit                                                       ║
      ╚════════════════════════════════════════════════════════════════╝

4. Complete the recommended setup steps in order:

   - **a) Change hostname** (e.g., ``ad-r1m-0``, ``ad-r1m-1``)
   - **b) Connect to WiFi** and note the IP address shown after connection
   - **c) Download latest docker image** (requires Cloudsmith login)
   - **d) Write CAN adapter firmware** (required for motor control)
   - **e) Write default motor tuning** (required for proper motor operation)
   - **f) Bind radio receiver** (optional, only if using RC control)

5. Verify SSH access from your host PC:

   .. code-block:: bash

      ssh analog@<robot-ip-address>

.. _docker-setup:

Docker Setup
~~~~~~~~~~~~

The AD-R1M software runs in Docker containers for isolation and reproducibility.

Verify Docker is running:

.. code-block:: bash

   sudo systemctl status docker
   docker ps

Pull the latest AD-R1M container:

.. code-block:: bash

    # Option 1: Use the recreate script (recommended)
    ~/recreate_container.sh
    
    # Option 2: Manual pull and tag
    IMAGE=docker.cloudsmith.io/adi/adrd-common/ad-r1m:rpi5-ftc2025
    docker pull $IMAGE
    docker tag $IMAGE working

Software Operation
------------------

For basic operation (power on, SSH, bringup), see the :doc:`quick-start-guide`.

.. _bringup-configuration:

Bringup Configuration
~~~~~~~~~~~~~~~~~~~~~

The ``bringup.sh`` script accepts environment variables to configure the robot stack:

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Default
     - Options
   * - ``RMW_IMPLEMENTATION``
     - ``rmw_zenoh_cpp``
     - ``rmw_zenoh_cpp`` (recommended), ``rmw_fastdds_cpp``
   * - ``TELEOP``
     - ``radio``
     - ``radio``, ``keyboard``, ``autonomous``
   * - ``LOCALIZATION``
     - ``blind``
     - ``blind`` (dead reckoning), ``amcl`` (map-based)
   * - ``NAVIGATION``
     - *(none)*
     - *(empty)* or ``nav2``
   * - ``ROBOT_NAMESPACE``
     - hostname-based
     - e.g., ``ad_r1m_0``, ``ad_r1m_1``

Example configurations:

.. code-block:: bash

   # Manual radio control (default)
   ~/bringup_radio.sh
   # Equivalent to: TELEOP=radio LOCALIZATION=blind ~/bringup.sh

   # Autonomous navigation with AMCL
   ~/bringup_amcl.sh
   # Equivalent to: TELEOP=radio LOCALIZATION=amcl NAVIGATION=nav2 ~/bringup.sh

   # Custom configuration
   TELEOP=keyboard LOCALIZATION=amcl NAVIGATION=nav2 ~/bringup.sh

For the complete list of bringup scripts, see :ref:`bringup-scripts-table` in the Quick Start Guide.

Starting Services Manually
~~~~~~~~~~~~~~~~~~~~~~~~~~

Start specific Docker Compose profiles:

.. code-block:: bash

   cd ~/ros2_ws
   
   # Basic robot with radio control
   docker compose --profile rmw_zenoh --profile teleop_radio --profile localization_blind up
   
   # With navigation
   docker compose --profile rmw_zenoh --profile teleop_radio --profile localization_amcl --profile navigation_nav2 up
   
   # Mapping mode
   docker compose --profile rmw_zenoh --profile teleop_radio --profile mapping up

Start individual services:

.. code-block:: bash

   docker compose up motors        # Just motors
   docker compose up motors imu    # Motors and IMU

Verifying Operation
~~~~~~~~~~~~~~~~~~~

Check running containers:

.. code-block:: bash

   docker ps

Access a running container:

.. code-block:: bash

   docker exec -it ad-r1m-motors-1 bash
   source /opt/ros/humble/setup.bash
   source /ros2_ws/install/setup.bash

Verify ROS 2 nodes:

.. code-block:: bash

   ros2 node list

Expected nodes include:

- ``/<namespace>/controller_manager``
- ``/<namespace>/diff_drive_controller``
- ``/<namespace>/imu_node``
- ``/<namespace>/tof_camera_node``

RViz Visualization
~~~~~~~~~~~~~~~~~~

For RViz setup on your host PC, see :ref:`ros2-visualization`.

.. _docker-compose-architecture:

Docker Compose Architecture
---------------------------

The system uses Docker Compose with profiles for modular service management.

Always-On Services
~~~~~~~~~~~~~~~~~~

These services start with every bringup configuration:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Service
     - Function
     - Key Details
   * - ``motors``
     - Motor control via CANopen
     - Requires ``NET_ADMIN`` capability
   * - ``imu``
     - ADIS16470 IMU sensor
     - Requires ``privileged: true``
   * - ``tof``
     - ADTF3175D ToF camera
     - Depth image publisher
   * - ``tof_republish``
     - Topic relay
     - Republishes to namespaced topics

Profile-Based Services
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Service
     - Profile
     - Function
   * - ``rmw_zenoh_router``
     - ``rmw_zenoh``
     - Zenoh middleware router
   * - ``rmw_fastdds_ds``
     - ``rmw_fastdds``
     - Fast-DDS discovery server
   * - ``teleop_radio``
     - ``teleop_radio``
     - CRSF/ELRS radio control
   * - ``teleop_autonomous``
     - ``teleop_autonomous``
     - Keyboard teleop
   * - ``mapping``
     - ``mapping``
     - SLAM Toolbox
   * - ``loc_blind``
     - ``localization_blind``
     - Dead reckoning (static TF)
   * - ``loc_amcl``
     - ``localization_amcl``
     - AMCL localization
   * - ``map_server``
     - ``map_server``
     - Serves static maps
   * - ``nav2``
     - ``navigation_nav2``
     - Nav2 navigation stack

Volume Mounts
~~~~~~~~~~~~~

Configuration and map data stored on host:

- ``/home/analog/ros_data:/ros_data``
- Maps: ``/ros_data/maps/``
- Parameters: ``/ros_data/navigation_params.yaml``, ``/ros_data/mapping_params.yaml``

ROS 2 Components
----------------

For detailed ROS 2 architecture documentation, see :doc:`software-guide/ros2-architecture`.

IMU (ADIS16470)
~~~~~~~~~~~~~~~

- **Topics**: ``/${NAMESPACE}/imu`` (sensor_msgs/Imu)
- **Interface**: IIO (Industrial I/O)
- **Frequency**: 200 Hz (default), configurable up to 2000 Hz

.. figure:: figures/imu_link.png
   :alt: IMU Link Position
   :align: center
   :width: 400px

   IMU coordinate frame on the robot

ToF Camera (ADTF3175D)
~~~~~~~~~~~~~~~~~~~~~~

- **Topics**: ``/cam1/depth_image`` (16UC1), ``/${NAMESPACE}/cam1/scan`` (LaserScan)
- **Interface**: USB via ADI ToF SDK
- **Function**: Depth images converted to 2D LaserScan for navigation

.. figure:: figures/fig_tof_tf.png
   :alt: ToF Camera Transform
   :align: center
   :width: 400px

   ToF camera coordinate frame

Motor Control (CANopen)
~~~~~~~~~~~~~~~~~~~~~~~

- **Topics**: Subscribes to ``cmd_vel``, publishes ``odom``
- **Interface**: CANopen via ``slcan0``
- **Framework**: ros2_control with differential drive controller

CRSF Remote Control
~~~~~~~~~~~~~~~~~~~

- **Topics**: ``/${NAMESPACE}/cmd_vel_joy``, ``/${NAMESPACE}/killswitch``
- **Device**: ``/dev/ttyCRSF``
- **Channels**: Right stick for motion, SA switch for killswitch

Development and Debugging
-------------------------

Viewing Logs
~~~~~~~~~~~~

.. code-block:: bash

   # All services
   docker compose logs -f

   # Specific service
   docker compose logs -f motors

   # With timestamps
   docker compose logs -f --timestamps motors

Restart Services
~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker compose restart motors
   docker compose restart imu tof

Interactive Container
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start interactive session
   docker compose run --rm motors bash

   # Access running container
   docker exec -it ad-r1m-motors-1 bash

For troubleshooting common issues, see :doc:`how-to/troubleshooting`.

Detailed Guides
---------------

.. seealso::

   - :doc:`tutorial/ros2-getting-started` - Getting started with ROS 2 on the AD-R1M
   - :doc:`tutorial/ros2-examples` - ROS 2 example applications
   - :doc:`explanation/ros2-architecture` - ROS 2 software architecture

