.. _getting-started:

AD-R1M Quick Start Guide
========================

This guide will help you power on, connect to, and operate the AD-R1M robot for the first time.

.. contents:: Table of Contents
   :depth: 2
   :local:

.. important::

   **First-Time Setup Required?**
   
   All robots built by Analog Devices come with their SD cards already prepared with the robot software, and you don't need to flash anything. If you are building an AD-R1M yourself or want to reinitialize your robot software from scratch, complete these steps first:
   
   - :ref:`sd-card-setup` - Flash the ADI Kuiper Linux image to your SD card
   - :ref:`first-boot-configuration` - Configure hostname, WiFi, firmware, and motor tuning
   
   See the :ref:`software-guide` for complete installation instructions.

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

Remote Control
--------------

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

Connect to the robot using SSH
------------------------------

Connecting to the robot using SSH allows you to:

- Configure a WiFi connection
- Reconfigure ROS 2 runtime
- Debug and troubleshoot robot software
- Deploy your own code to the robot

If you haven't yet configured WiFi, you must connect to the AD-R1M through the wired Ethernet port in the back. Once you configure WiFi, you may disconnect the Ethernet cable, to let your robot roam free.

.. note::

   In the following sections, ``ad-r1m-123`` represents the hostname of your robot and the ``123`` should be replaced with your actual number, e.g. ``ad-r1m-6``, ``ad-r1m-42``, ...

Run:

.. shell::

  $ ssh analog@ad-r1m-123.local

Username: ``analog``

Password: ``analog``

Connect the robot to your WiFi network
--------------------------------------

#. Connect to the AD-R1M using SSH
#. Run ``sudo nmtui`` (password ``analog``)
#. Enter the "Activate a connection" menu
#. Select your WiFi network from the list
#. Enter the WiFi password
#. Verify the connection -- does your network have an ``*`` (asterisk) next to it?
#. Press :kbd:`Escape` 3 times to exit ``nmtui``

Prepare software on your computer
---------------------------------

The robot stack runs standalone and doesn't depend on any external software. You may install extra software on your computer for:

* Remotely visualizing the robot's perceived environment
* Sending commands to the autonomous navigation function
* Running ROS 2 code that communicates with the robot

Our recommended mechanism for this is to use `Pixi <https://pixi.prefix.dev/latest/>`__. First install Pixi by following their `installation guide <https://pixi.prefix.dev/latest/installation/>`__, i.e.:

   .. tab-set::

      .. tab-item:: Linux & Max

         In a terminal window, run:

         .. shell::

            $ curl -fsSL https://pixi.sh/install.sh | sh
         
         Close and reopen the terminal window, or run ``source ~/.bashrc`` (or the rc of your shell of choice).

      .. tab-item:: Windows

         In a powershell window, run:

         .. shell::

            $ powershell -ExecutionPolicy Bypass -c "irm -useb https://pixi.sh/install.ps1 | iex"
         
         Close and reopen the powershell window.

Then create a Pixi workspace:

   .. shell::

      $ pixi init pixiws -c robostack-humble -c conda-forge
      $ cd pixiws

   .. tip::

      You may change ``pixiws`` in these first two commands to something else -- it is just a folder name.

   .. shell::

      ~/pixiws
      $ pixi add ros-humble-desktop ros-humble-rmw-zenoh-cpp
      $ pixi workspace activation env set RMW_IMPLEMENTATION="rmw_zenoh_cpp"
      $ pixi workspace activation env set ZENOH_CONFIG_OVERRIDE="connect/endpoints=['tcp/ad-r1m-123.local:7447'];mode='client'"


   .. note::

      Be careful to change the ``ad-r1m-123`` in the last command to your ``ad-r1m-...`` number. You may run these commands multiple times, to overwrite previous settings.

Visualize the robot using Rviz
------------------------------

Rviz is the standard ROS tool for listening to live data from a robot and displaying it in a 3D environment.

In the Pixi workspace folder, run:

.. shell::

   ~/pixiws
   pixi run rviz2

Out of the box, rviz doesn't display much:

.. figure:: /figures/rviz_empty.png
   :alt: RViz with default empty configuration
   :align: center
   :width: 800px

You may build visualizations by adding display items using the "Add" button in the bottom left. Alternatively, you can download our :download:`ready made rviz configuration file <../../../ad_r1m_description/rviz/main.rviz>` and open it from the Rviz ``File`` > ``Open Config`` menu, which should look something like this:

.. figure:: /figures/rviz_example.png
   :alt: RViz with an example configuration showing the robot 3D model and its camera views
   :align: center
   :width: 800px

Note that the ToF preview will always be upside down because of the sensor's position. The robot model encodes this orientation information, so all ROS nodes that use ToF data know to "untwist" it -- this is just a visualization quirk.

Control the robot using a keyboard
----------------------------------

In development, it is often useful to quickly teleoperate the robot without using the physical remote control, for which you can use ROS' ``teleop_twist_keyboard``. In the Pixi workspace folder, run:

.. shell::

   ~/pixiws
   $ pixi run ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=cmd_vel_joy

   Moving around:
      u    i    o
      j    k    l
      m    ,    .

Next Steps
----------

Now that your robot is operational, explore these capabilities:

.. grid::
   :columns: 2

   .. card::
      :ref: mapping-with-slam

      **Mapping** -- Create maps of your environment

      .. figure:: /figures/do_mapping.gif
          :align: center
          :width: 100%

   .. card::
      :ref: autonomous-navigation
      
      **Navigation** -- Autonomous navigation to goals

      .. figure:: /figures/navigate.gif
          :align: center
          :width: 100%


- **Create a map**: See :ref:`mapping-with-slam`
- **Navigate autonomously**: See :ref:`autonomous-navigation`
- **Understand the architecture**: See :ref:`ros2-architecture`
- **Troubleshoot issues**: See :ref:`troubleshooting`
