AD-R1M Troubleshooting
======================

.. contents:: Table of Contents
   :depth: 2
   :local:

This page provides solutions to common issues encountered when operating the AD-R1M robot.

.. _rc-troubleshooting:

Remote Control Issues
---------------------

Radio Connection Problems
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Problem
     - Solution
   * - No bars on RC screen
     - Check robot is powered on and ``bringup_radio.sh`` is running
   * - "NO DATA" on telemetry
     - Verify CRSF transceiver power (GPIO 24), check ``/dev/ttyCRSF`` device
   * - RxBt blinking
     - Wait for ROS2 stack to fully initialize (~30 seconds)
   * - Robot doesn't move when armed
     - Check killswitch position, verify motor service is running: ``docker compose logs motors``

Telemetry Status Interpretation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Status
     - RxBt Display
     - Description
   * - Radio not connected
     - "NO DATA" message
     - No communication with robot
   * - Connected, no ROS 2 data yet
     - RxBt blank or blinking
     - Connection established but ROS2 stack not publishing
   * - Fully functional
     - RxBt shows robot system voltage
     - Full telemetry operational (e.g., "12.3V")

.. caution::

   Ensure RxBt (robot battery voltage) does not drop below **9V** during operation.

CAN Interface Issues
--------------------

If motor control fails, check the CAN interface:

.. code-block:: bash

   ip link show slcan0
   candump slcan0

Reset CAN interface (handled by bringup script):

.. code-block:: bash

   sudo ~/recan.sh

Common CAN Error Messages
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Error
     - Solution
   * - ``slcan0: link is not ready``
     - Run ``sudo ~/recan.sh`` to reinitialize CAN interface
   * - ``No CAN devices found``
     - Check USB-CAN adapter connection, verify ``slcand`` service is running
   * - CANopen initialization timeout
     - Restart the motors service: ``docker compose restart motors``

IMU Issues
----------

IMU Not Publishing
~~~~~~~~~~~~~~~~~~

Verify IIO device is accessible:

.. code-block:: bash

   iio_info -u ip:localhost | grep adis16470

Check sampling frequency:

.. code-block:: bash

   iio_attr -u ip:localhost -d adis16470 sampling_frequency

Common IMU Issues
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - Solution
   * - No ``adis16470`` device found
     - Check SPI connection, verify kernel module is loaded: ``lsmod | grep adis``
   * - IMU data frozen
     - Restart iiod service: ``sudo systemctl restart iiod``
   * - High noise in IMU readings
     - Check mounting, ensure IMU is securely attached to chassis

ToF Camera Issues
-----------------

Camera Not Working
~~~~~~~~~~~~~~~~~~

Ensure media configuration script has run:

.. code-block:: bash

   sudo systemctl status media-config.service

Check depth image topic:

.. code-block:: bash

   docker exec -it adrd_demo_ros2-tof-1 bash -c "source /ros2_ws/install/setup.bash && ros2 topic hz /cam1/depth_image"

Common Camera Issues
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - Solution
   * - No depth image published
     - Run ``~/Workspace/media_config_16D_16AB_8C.sh`` and restart tof container
   * - Camera shows all zeros
     - Check USB connection, verify camera is powered
   * - Low frame rate
     - Check CPU usage, reduce resolution if needed
   * - ``/cam1/scan`` empty
     - Verify ``depthimage_to_laserscan`` node is running

Docker Container Issues
-----------------------

Container Not Starting
~~~~~~~~~~~~~~~~~~~~~~

Check container logs:

.. code-block:: bash

   docker compose logs motors

Verify profiles are enabled:

.. code-block:: bash

   echo $COMPOSE_PROFILES

Common Docker Issues
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - Solution
   * - Container exits immediately
     - Check logs for error messages, verify device permissions
   * - ``Permission denied`` errors
     - Ensure proper Docker flags (``--privileged``, ``--cap-add``)
   * - Network issues between containers
     - Verify ``--network=host`` is set
   * - Container can't access devices
     - Check ``--device`` flags, verify device exists on host

Restart Services
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Restart specific service
   docker compose restart motors

   # Restart all services
   docker compose down && docker compose up -d

   # Full system restart
   sudo reboot

Navigation Issues
-----------------

Navigation Not Working
~~~~~~~~~~~~~~~~~~~~~~

Verify map is loaded:

.. code-block:: bash

   ros2 topic echo --once /${ROBOT_NAMESPACE}/map

Check AMCL pose estimate:

.. code-block:: bash

   ros2 topic echo /${ROBOT_NAMESPACE}/amcl_pose

Ensure costmaps are being published:

.. code-block:: bash

   ros2 topic list | grep costmap

Common Navigation Problems
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - Solution
   * - Robot doesn't move to goal
     - Check ``/cmd_vel_nav`` is being published, verify twist_mux priority
   * - Path planning fails
     - Ensure goal is in free space on the costmap
   * - Robot oscillates near goal
     - Tune DWB controller ``xy_goal_tolerance`` and ``yaw_goal_tolerance``
   * - AMCL not converging
     - Set initial pose in RViz, drive robot to help particle filter converge
   * - Costmap shows incorrect obstacles
     - Check LaserScan data, verify TF transforms are correct

Localization Issues
~~~~~~~~~~~~~~~~~~~

If AMCL localization is poor:

1. **Set a good initial pose** using RViz's "2D Pose Estimate" tool
2. **Drive the robot** to help particles converge
3. **Check the map** matches the current environment
4. **Verify LaserScan** data is being received correctly

Transform (TF) Issues
---------------------

Check TF Tree
~~~~~~~~~~~~~

.. code-block:: bash

   ros2 run tf2_tools view_frames

This generates a PDF showing the complete transform tree.

Common TF Errors
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Error
     - Solution
   * - ``Could not transform...``
     - Check if the publishing node is running
   * - ``Lookup would require extrapolation into the past``
     - Time synchronization issue, check NTP or use ``use_sim_time`` parameter
   * - ``map`` frame not found
     - Start localization or mapping node
   * - Duplicate TF publishers
     - Ensure only one node publishes each transform

Network and Communication Issues
--------------------------------

RViz Can't Connect to Robot
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Check network connectivity**:

   .. code-block:: bash

      ping ad-r1m-0.local

2. **Verify Zenoh router is running**:

   .. code-block:: bash

      docker compose logs rmw_zenoh_router

3. **Check RMW implementation**:

   .. code-block:: bash

      echo $RMW_IMPLEMENTATION

Topics Not Visible
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all topics
   ros2 topic list

   # Check if node is publishing
   ros2 topic info /topic_name

   # Check topic frequency
   ros2 topic hz /topic_name

Power and Battery Issues
------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - Solution
   * - Robot won't power on
     - Press silver button to enable battery, then press green button to start
   * - Robot shuts down unexpectedly
     - Battery voltage too low (below 9V), charge immediately
   * - LED not blinking
     - Check battery connection, verify BMS is functioning
   * - Motors not responding after power-on
     - Wait for full boot sequence (~45s), check bringup script status

System Recovery
---------------

Full System Reset
~~~~~~~~~~~~~~~~~

If the robot is unresponsive:

1. **SSH into the robot** (if possible):

   .. code-block:: bash

      ssh analog@ad-r1m.local
      sudo reboot

2. **If SSH fails**, power cycle the robot:

   - Press silver button to cut battery power
   - Wait 10 seconds
   - Press silver button again to enable battery
   - Press green button to restart

Reflashing the SD Card
~~~~~~~~~~~~~~~~~~~~~~

If the system is corrupted:

1. Download the latest AD-R1M image
2. Flash to SD card using Raspberry Pi Imager or ``dd``
3. Boot the robot with the new SD card
4. Reconfigure WiFi and hostname as needed

Getting Help
------------

If you cannot resolve an issue:

1. **Collect logs**:

   .. code-block:: bash

      docker compose logs > robot_logs.txt

2. **Capture system state**:

   .. code-block:: bash

      ros2 topic list > topics.txt
      ros2 node list > nodes.txt

3. **Post on Engineer Zone**: Visit the `ADI Engineer Zone <https://ez.analog.com/>`__ with your logs and a description of the issue
