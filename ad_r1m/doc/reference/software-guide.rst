.. _software-guide:

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

For instructions on setting up the SD card and installing the AD-R1M system software, see :ref:`setup-rpi`.

.. _first-boot-configuration:

First Boot Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

The AD-R1M robot is pre-configured and starts automatically on boot.

1. Login with default credentials:

   - Username: ``analog``
   - Password: ``analog``

2. The robot automatically initializes hardware via systemd services:

   - ``ad-r1m-slcan.service`` - CAN adapter initialization
   - ``ad-r1m-crsf.service`` - CRSF radio receiver initialization
   - ``ad-r1m-imu.service`` - IMU sampling frequency configuration
   - ``ad-r1m-tof.service`` - ToF camera reset
   - ``ad-r1m-bringup.service`` - Docker Compose startup

3. Configure WiFi (optional):

   .. code-block:: bash

      sudo nmtui

4. Verify SSH access from your host PC:

   .. code-block:: bash

      ssh analog@ad-r1m-<number>.local

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

    docker pull docker.cloudsmith.io/adi/adrd-common/ad-r1m:robot-humble-nightly

Software Operation
------------------

For basic operation (power on, SSH, bringup), see the :ref:`getting-started`.

.. _bringup-configuration:

AD-R1M CLI
~~~~~~~~~~

The ``ad-r1m`` command-line tool manages robot configurations:

**ad-r1m mkconfig <folder>**

Creates a new configuration folder from the default template:

.. code-block:: bash

   ad-r1m mkconfig nav
   cd nav
   ls
   # ad-r1m.env  compose.yaml  ros_data/

**ad-r1m enable <folder>**

Sets a configuration folder to auto-start at boot:

.. code-block:: bash

   ad-r1m enable ~/nav
   # Requires sudo, edits systemd service

**Environment Variables**

Configuration is controlled via ``ad-r1m.env``:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Variable
     - Default
     - Description
   * - ``RMW_IMPLEMENTATION``
     - ``rmw_zenoh_cpp``
     - ROS 2 middleware (rmw_zenoh_cpp, rmw_fastrtps_cpp)
   * - ``DOCKER_IMAGE``
     - ``docker.cloudsmith.io/adi/adrd-common/ad-r1m:robot-humble-nightly``
     - Docker image for ROS 2 containers
   * - ``ROBOT_NAMESPACE``
     - ``/``
     - Robot namespace for multi-robot setups
   * - ``COMPOSE_PROJECT_NAME``
     - ``ad-r1m``
     - Docker Compose project name

Starting Services Manually
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``ad-r1m mkconfig`` to generate a configuration folder, then start services with Docker Compose:

.. code-block:: bash

   # Generate configuration
   ad-r1m mkconfig nav
   cd nav

   # Start base services (robot, tof, teleop, zenoh)
   docker compose --env-file ad-r1m.env up -d

   # Start SLAM for mapping
   docker compose --env-file ad-r1m.env up -d slam

   # Start localization (AMCL with map)
   docker compose --env-file ad-r1m.env up -d localization_amcl

   # Start localization (blind/dead-reckoning)
   docker compose --env-file ad-r1m.env up -d localization_blind map_server

   # Start navigation
   docker compose --env-file ad-r1m.env up -d nav

   # Save map after mapping
   docker compose --env-file ad-r1m.env run save_map

   # Keyboard teleop (interactive)
   docker compose --env-file ad-r1m.env run --rm teleop_keyboard

Start individual development services:

.. code-block:: bash

   # Motors only (with sensor_fusion)
   docker compose --env-file ad-r1m.env up -d motors sensor_fusion

   # IMU only
   docker compose --env-file ad-r1m.env up -d imu

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

The system uses Docker Compose with services and profiles for modular service management.

Base Services (No Profile)
~~~~~~~~~~~~~~~~~~~~~~~~~~

These services start with ``docker compose --env-file ad-r1m.env up -d``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Service
     - Function
     - Key Details
   * - ``zenoh_router``
     - Zenoh middleware router
     - Profile: ``rmw_zenoh_cpp``
   * - ``robot``
     - Motor control, IMU, odometry, sensor fusion
     - Launches ``bringup.launch.py``
   * - ``tof``
     - Depth to LaserScan conversion
     - Receives depth from ToF camera module
   * - ``teleop_crsf``
     - CRSF/ELRS radio control
     - Requires ``/dev/ttyCRSF``

Profile-Based Services
~~~~~~~~~~~~~~~~~~~~~~

Start with ``docker compose --env-file ad-r1m.env up -d <service>``:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Service
     - Profile
     - Function
   * - ``slam``
     - ``slam``
     - SLAM Toolbox for mapping
   * - ``localization_amcl``
     - ``loc_amcl``
     - AMCL localization (requires map)
   * - ``localization_blind``
     - ``loc_blind``
     - Dead reckoning (static TF)
   * - ``map_server``
     - ``loc_blind``
     - Serves empty map for blind localization
   * - ``nav``
     - ``nav``
     - Nav2 navigation stack
   * - ``motors``
     - ``motors``
     - Motor control only (development)
   * - ``sensor_fusion``
     - ``motors``
     - EKF sensor fusion (development)
   * - ``imu``
     - ``imu``
     - IMU only (development)

One-Off Services
~~~~~~~~~~~~~~~~

Run with ``docker compose --env-file ad-r1m.env run <service>``:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Service
     - Function
   * - ``teleop_keyboard``
     - Interactive keyboard teleop with killswitch control
   * - ``save_map``
     - Save current map to ``ros_data/maps/``
   * - ``shell``
     - Interactive shell inside container

Volume Mounts
~~~~~~~~~~~~~

Configuration and data stored in ``ros_data/``:

- ``ros_data/maps/`` - Saved maps
- ``ros_data/navigation_params.yaml`` - Nav2 parameters
- ``ros_data/mapper_params_online_async.yaml`` - SLAM parameters
- ``ros_data/teleop_parameters.yaml`` - Teleop parameters
- ``ros_data/ekf.yaml`` - EKF sensor fusion parameters
- ``ros_data/log/`` - ROS 2 logs

ROS 2 Components
----------------

For detailed ROS 2 architecture documentation, see :ref:`ros2-architecture`.

IMU (ADIS16470)
~~~~~~~~~~~~~~~

- **Topics**: ``/${NAMESPACE}/imu`` (sensor_msgs/Imu)
- **Interface**: IIO (Industrial I/O)
- **Frequency**: 200 Hz (default), configurable up to 2000 Hz

.. figure:: /res/imu_link.png
   :alt: IMU Link Position
   :align: center
   :width: 400px

   IMU coordinate frame on the robot

ToF Camera (ADTF3175D)
~~~~~~~~~~~~~~~~~~~~~~

- **Topics**: ``/cam1/depth_image`` (16UC1), ``/scan`` (LaserScan)
- **Interface**: Runs on dedicated ToF compute module, communicates via Zenoh
- **Function**: Depth images converted to 2D LaserScan on robot for navigation

.. figure:: /res/fig_tof_tf.png
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
   docker compose --env-file ad-r1m.env logs -f

   # Specific service
   docker compose --env-file ad-r1m.env logs -f robot

   # With timestamps
   docker compose --env-file ad-r1m.env logs -f --timestamps robot

   # Docker logs directly
   docker logs ad-r1m-robot-1

Restart Services
~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker compose --env-file ad-r1m.env restart robot
   docker compose --env-file ad-r1m.env restart tof

Stop All Services
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Stop compose services
   docker compose --env-file ad-r1m.env down

   # Stop all running containers
   docker stop $(docker ps -q)

Interactive Container
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start interactive shell
   docker compose --env-file ad-r1m.env run --rm shell bash

   # Access running container
   docker exec -it ad-r1m-robot-1 bash

For troubleshooting common issues, see :ref:`troubleshooting`.

Detailed Guides
---------------

.. seealso::

   - :ref:`ros2-getting-started` - Getting started with ROS 2 on the AD-R1M
   - :ref:`ros2-examples` - ROS 2 example applications
   - :ref:`ros2-architecture` - ROS 2 software architecture

