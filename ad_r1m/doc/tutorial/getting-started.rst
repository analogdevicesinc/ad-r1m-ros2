AD-R1M Quick Start Guide
========================

This guide will help you power on, connect to, and operate the AD-R1M robot for the first time.

.. contents:: Table of Contents
   :depth: 2
   :local:

.. important::

   **First-Time Setup Required?**
   
   If your SD card is not pre-flashed or you need to configure the robot for the first time, complete these steps first:
   
   - :ref:`sd-card-setup` - Flash the ADI Kuiper2 image to your SD card
   - :ref:`first-boot-configuration` - Configure hostname, WiFi, firmware, and motor tuning
   
   See the :doc:`software-guide` for complete installation instructions.

Power On
--------

.. figure:: /figures/robot-buttons.png
   :alt: Robot side panel
   :align: center
   :width: 500px

   Robot Control Panel

1. **Press the gray latching button** to engage the battery cut-off relay
2. **Press and hold the gray momentary button** (~1s) to start the robot electronics
3. **Wait for the LED ring** to turn solid green (~60 seconds)

.. list-table:: LED Status Codes
   :header-rows: 1
   :widths: 20 25 55

   * - Time
     - Pattern
     - Meaning
   * - ~5s
     - ▄ ▄▄▄ ▄ ▄
     - Linux boot started
   * - ~45s
     - ▄ ▄ ▄▄▄ ▄
     - Bringup script starting
   * - ~60s
     - Solid green
     - System ready

.. note::

   On boot, the robot automatically starts the motors, sensors, and RC teleop nodes. 
   Once the LED turns solid green, you can immediately control the robot using the RC handset.

Remote Control (RC)
-------------------

.. figure:: /figures/rc.png
   :alt: RC Interface
   :align: center
   :width: 600px

   Radio controller showing buttons, switches, and joysticks

**Step 1: Verify Connection**

Press **[RTN]** to return to the home screen. Look for the wireless "bars" icon indicating connection.

.. figure:: /figures/radio_connect.png
   :alt: RC Connection Status
   :align: center
   :width: 500px

   Radio connection status: disconnected (left) vs connected (right)

**Step 2: Check Telemetry**

Press **[TELE]** to view the telemetry screen. RxBt should display the battery voltage (e.g., "12.3V").

.. warning::

   Do not let battery voltage drop below **9V** during operation.

**Step 3: Arm the Robot**

Move the **arm switch (SA)** to the "ARMED" (down) position. The robot should shake slightly to confirm.

.. figure:: /figures/killswitch.png
   :alt: Killswitch Position
   :align: center
   :width: 400px

   Arm switch positions: OFF (up) = safe, ARMED (down) = active

**Step 4: Drive**

Use the **right control gimbal**:

- **Forward/Back**: Stick up/down
- **Turn**: Stick left/right
- **Stop**: Release to center

For initial RC setup and binding the receiver, see :ref:`first-boot-configuration`.

For RC troubleshooting, see :ref:`rc-troubleshooting`.

Connect via SSH
---------------

For advanced usage, debugging, or running different operational modes, connect to the robot via SSH.

1. **SSH into the robot**:

   .. code-block:: bash

      ssh analog@ad-r1m-0.local

   - **Hostname**: Replace ``ad-r1m-0`` with your robot's hostname
   - **Credentials**: ``analog`` / ``analog``

2. **View running services** (optional):

   .. code-block:: bash

      docker compose ps

.. _bringup-scripts-table:

Alternative Bringup Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default boot configuration starts radio teleop mode. To use different modes, stop the current stack and start a different one:

.. code-block:: bash

   # Stop current services
   docker compose down

   # Start a different mode
   ./bringup_mapping.sh

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Script
     - Control Mode
     - Description
   * - ``./bringup_radio.sh``
     - Radio
     - Manual teleoperation with RC handset (default)
   * - ``./bringup_keyboard.sh`` + ``./teleop.sh``
     - Keyboard
     - Development/testing without radio
   * - ``./bringup_mapping.sh``
     - Radio + SLAM
     - Create maps of new environments
   * - ``./bringup_amcl.sh``
     - Radio + Nav2
     - Autonomous navigation in mapped environment
   * - ``./bringup_blind.sh``
     - Radio + Nav2
     - Autonomous navigation without pre-existing map

For detailed bringup configuration options, see :doc:`software-guide`.

Keyboard Control
----------------

For development without the RC handset:

1. Start core services: ``./bringup_keyboard.sh``
2. In a new terminal: ``./teleop.sh``
3. Press ``p`` to arm, then use keyboard to drive

.. code-block:: text

   Controls:  u i o     q/z: speed ±10%
              j k l     p: arm | r: disarm
              m , .     CTRL-C: quit

Visualize with RViz
-------------------

View robot data from your host PC. For complete setup instructions including ROS 2 installation, see :doc:`software-guide/ros2-getting-started`.

**Quick Start** (if ROS 2 and Zenoh RMW are already installed):

.. code-block:: bash

   cd platform/common/scripts
   ./start_rviz.sh 0

.. figure:: /figures/rviz_view.png
   :alt: RViz Visualization
   :align: center
   :width: 800px

   RViz visualization of AD-R1M robot

Next Steps
----------

Now that your robot is operational, explore these capabilities:

.. list-table::
   :widths: 50 50
   :class: borderless

   * - .. figure:: /figures/do_mapping.gif
          :align: center
          :width: 100%

          **Mapping** - Create maps of your environment

     - .. figure:: /figures/navigate.gif
          :align: center
          :width: 100%

          **Navigation** - Autonomous navigation to goals

- **Create a map**: See :ref:`mapping-with-slam`
- **Navigate autonomously**: See :ref:`autonomous-navigation`
- **Understand the architecture**: See :doc:`software-guide/ros2-architecture`
- **Troubleshoot issues**: See :doc:`troubleshooting`
