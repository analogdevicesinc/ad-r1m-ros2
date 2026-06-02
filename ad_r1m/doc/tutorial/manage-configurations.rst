Manage AD-R1M runtime configurations
====================================

This tutorial covers how to create, edit, and manage multiple runtime configuration folders for the AD-R1M.

Right after installation, the AD-R1M software only starts up a basic teleoperation application, with no advanced functions active, such as mapping, navigation, etc. **Runtime configuration folders** are a self-contained, version controllable format that allows you to adjust the robot software by:

* enabling or disabling various builtin functions
* starting up your own ROS 2 nodes
* changing parameter files
* providing data files such as maps for navigation
* etc.

Their structure is simple, consisting of:

* ``compose.yaml`` -- a standard docker compose file describing what containers to start up
* ``ad-r1m.env`` -- a file containing environment variables to pass to the software, in ``KEY=VALUE`` format
* ``ros_data/`` -- a folder containing all data we want to provide to the containers (e.g. parameters, maps) and/or persist from the containers (e.g. logs, rosbags)
   * ``log/`` -- ROS 2 runtime logs. Mounted to ``~/.ros/log`` inside the containers.
   * ``*parameters.yaml`` -- ROS 2 parameter files
   * ...

Create a runtime configuration
------------------------------

As an illustrative example, we will create a runtime configuration that uses **keyboard teleoperation** instead of the default **hardware remote control teleoperation**.

You need to be connected to the robot for all of the following steps.

To get started, create the config folder from the default:

.. shell::

   $ ad-r1m mkconfig keyboard-teleop-config

Take a look inside the folder and notice the structure from the previous section:

.. shell::

   $ cd keyboard-teleop-config
   $ ls
   ad-r1m.env
   compose.yaml
   ros_data

Edit a runtime configuration
----------------------------

``compose.yaml`` is a standard docker compose file describing what containers to start.

The default file contains three services: ``zenoh_router``, ``robot``, and ``teleop_crsf``.
We will remove ``teleop_crsf`` and replace it with a service running the ``teleop_twist_keyboard`` node.

Edit ``compose.yaml`` and make the following changes:

.. code-block:: diff

   -  teleop_crsf:
   +  teleop_keyboard:
        image: $DOCKER_IMAGE
        command: >
   -      ros2 launch ad_r1m_bringup teleop_crsf.launch.py
   -        namespace:="${ROBOT_NAMESPACE:-/}"
   -        params_file:="/ros_data/teleop_parameters.yaml"
   +      ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args
   +        --remap cmd_vel:=/cmd_vel_keyboard

   +    stdin_open: true
   +    tty: true
        network_mode: host
        ipc: host
        pid: host
   -    privileged: true
        volumes:
   -       - /dev/ttyCRSF:/dev/ttyCRSF
           - ./ros_data:/ros_data
           - ./ros_data/log:/root/.ros/log
        environment:
           - RMW_IMPLEMENTATION
        depends_on:
          zenoh_router:
            condition: "service_started"
            required: false

With these, we:

#. Change the container name from ``teleop_crsf`` to ``teleop_keyboard`` to be descriptive.
#. Change the command that runs from launching ``ad_r1m_bringup/teleop_crsf.launch.py`` to running ``teleop_twist_keyboard``.
#. Enable an interactive tty for this container -- the equivalent of the ``-i -t`` parameters for ``docker run``.
#. Remove the now unnecessary access to the ``/dev/ttyCRSF`` serial device.

Start a runtime configuration
-----------------------------

With everything set up, use ``docker compose up`` to start this configuration. Enter the configuration folder and run:

.. shell::

   $ cd keyboard-teleop-config
   $ docker compose --env-file ad-r1m.env up

For this example, because the keyboard teleop node requires interaction in the terminal, we will also need to attach to it. This will generally not be needed. To attach to it and start controlling the robot, run:

.. shell::

   $ docker logs ad-r1m-teleop_keyboard-1

   This node takes keypresses from the keyboard and publishes them
   as Twist/TwistStamped messages. It works best with a US keyboard layout.
   ---------------------------
   Moving around:
      u    i    o
      j    k    l
      m    ,    .

   For Holonomic mode (strafing), hold down the shift key:
   ---------------------------
      U    I    O
      J    K    L
      M    <    >

   t : up (+z)
   b : down (-z)

   anything else : stop

   q/z : increase/decrease max speeds by 10%
   w/x : increase/decrease only linear speed by 10%
   e/c : increase/decrease only angular speed by 10%

   CTRL-C to quit

   currently:      speed 0.50      turn 1.00

   $ docker attach ad-r1m-teleop_keyboard-1

To detach, press :kbd:`Ctrl+P` then :kbd:`Ctrl+Q`.

Set the runtime configuration to use at startup
-----------------------------------------------

Now that we have a working configuration, we can also point the startup service to launch this one instead of the default using ``ad-r1m enable``. Keep in mind that this requires elevated privileges because we're editing a system service:

.. shell::

   $ ad-r1m enable keyboard-teleop-config

At the next robot startup, you should notice that this configuration starts up because the hardware remote control isn't used.

As previously, to attach to the keyboard teleop container, run:

.. shell::

   $ docker attach ad-r1m-teleop_keyboard-1

Use the :kbd:`Ctrl+P Ctrl+Q` sequence to exit.

Providing parameter or data files
---------------------------------

Very commonly, you will need to provide parameters to custom nodes, or other kinds of data files (e.g. maps). For this, we just place any files we want to pass to the container in the ``ros_data`` folder, and they will appear in ``/ros_data`` inside the container.

As an example, let's create a file that changes the default speed for the keyboard teleop node:

.. shell::

   $ cd keyboard-teleop-config
   $ edit ros_data/teleop_params.yaml

   /**/teleop_keyboard:
     ros__parameters:
       max_vel: 1.0
       max_rot: 1.0
       stamped: false
       frame_id: ''

The file will be present inside the containers at ``/ros_data/teleop_params.yaml``. We must now also edit the command in the compose file to use this:

.. code-block:: diff

     teleop_keyboard:
       command: >
         ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args
           --remap cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
   +       --params-file /ros_data/teleop_params.yaml

Reading logs
------------

ROS 2 logs will be present both in the docker container logs, as well as stored in the ``ros_data/log/`` folder.
