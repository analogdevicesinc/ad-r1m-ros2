AD-R1M software system architecture
===================================

The AD-R1M and its variants require first- and third-party software to run on multiple layers to ultimately support a ROS 2 app:

* **Linux system and kernel**
* **Docker containers**
* **ROS 2 application layer**

This is an explanatory overview for each of these layers, what purpose they serve, what the AD-R1M project brings to each, and how they interact.

Linux system
------------

The AD-R1M runs `ADI Kuiper Linux <https://analogdevicesinc.github.io/kuiper/>`__, a Debian-based
distribution with built-in support for a large number of Analog Devices products.

The AD-R1M linux system layer provides:

* User utilities through the ``ad-r1m`` command
* systemd units for robot bringup after boot
* Udev rules
* Default robot configuration files
* Extra kernel modules and device tree overlays

Of these, some are consistent between robot variants, while others are variant-specific. To handle this, we split them into composable features:

* **common** - Files common to *all* AD-R1M variants
* **rpi5** - Support for variants using a Raspberry Pi 5 + ADRD4161
* **adrd3161** - Support for variants using the ADRD3161 motor drive
* etc.

Each of these gets a folder in ``system/`` which contains a rootfs "overlay" providing all files necessary for that feature, e.g.:

.. code-block::

   system/common/
   ├── usr
   │   ├── bin
   │   │   └── ad-r1m
   │   ├── lib
   │   │   ├── ad-r1m
   │   │   │   └── cli
   │   │   │       ├── start
   │   │   │       └── ...
   │   │   └── systemd
   │   │       └── system
   │   │   │       ├── ad-r1m.target
   │   │   │       ├── ad-r1m-bringup.service
   │   │   │       └── ...
   │   └── share
   │       └── ad-r1m
   │           └── default-config
   │               └── ...
   └── ...


These features are combined into debian packages by the packaging logic defined in ``packaging/debian/``. For example, the ``ad-r1m-system-rpi5`` package, which installs all system-level files for the main AD-R1M variant, is a combination of the ``common``, ``rpi5`` and ``adrd3161`` system features. These compositions are defined in ``packaging/debian/<package>.install``, e.g.:

.. code-block::

    # packaging/debian/ad-r1m-system-rpi5.install
    VERSION /usr/lib/ad-r1m/
    system/common/* /
    system/rpi5/* /
    system/adrd3161/* /

Bringup at boot
^^^^^^^^^^^^^^^

Automatic robot software startup is defined by the systemd unit ``ad-r1m.target``. Other units relate to it, and they can be split in two categories:

#. Units for setting up peripherals. In systemd terms, these are all ``PartOf``, ``WantedBy`` and ``Before`` ``ad-r1m.target``. That makes it so that all must be successful before ``ad-r1m.target`` is considered active, and restarting ``ad-r1m.target`` restarts them all.
#. The ``ad-r1m-bringup.service`` unit launches the Docker containers running the ROS app. This is ``PartOf`` and ``After`` ``ad-r1m.target``, meaning it will only start after all the previous hardware bringup units are done.

.. mermaid::

    flowchart LR

        tgt[ad-r1m.target]
        tgt -- Requires --> c1(80-can0.network<br>Configure CAN)
        tgt -- Requires --> c2(ad-r1m-imu.service<br>Configure IMU)
        tgt -- Requires --> c3(ad-r1m-crsf.service<br>Power up RC receiver)

        r[multi-user.target] -- Wants --> tgt
        br[ad-r1m-bringup.service<br>Start Docker containers] -- After --> tgt -- Before --> br
        r -- Wants --> br

ROS 2 reconfiguration
^^^^^^^^^^^^^^^^^^^^^

The ``ad-r1m start`` command looks in the current directory (or the directory specified as the first argument) for the following configuration files:

* ``ad-r1m.env`` -- Environment variables
* ``compose.yaml`` -- Docker compose file describing which containers to start up

The default ``compose.yaml`` uses the ``./ros_data`` directory (relative to the compose file) for persisting logs, configs, maps, etc. between runs. It is mounted to ``/ros_data/`` inside the containers.

The default configuration is present in ``/usr/share/ad-r1m/default-config`` and shouldn't be modified by users. To create an alternate configuration, use the ``ad-r1m mkconfig`` command and edit as you please:

.. shell::

    $ ad-r1m mkconfig my-config
    $ cd my-config

    $ edit ad-r1m.env
    ROS_DISTRO=jazzy

    $ edit compose.yaml
    ...

To start the robot software using that configuration, enter your configuration folder and run ``ad-r1m start``:

.. shell::

    $ cd my-config
    $ ad-r1m start

To automatically start an alternative configuration at boot-time, use ``ad-r1m enable <folder>``:

.. shell::

    $ sudo ad-r1m enable my-config

Behind the curtain, this adds an override for ``ad-r1m-bringup.service`` that changes its working directory:

.. code-block::

    # /etc/systemd/system/ad-r1m-bringup.service.d/override.conf
    [Service]
    WorkingDirectory=/home/analog/my-config/

.. seealso::

    The :doc:`/tutorial/manage-configurations` tutorial contains more practical examples of the functionality described above.



Docker containers
-----------------

Because ROS is "picky" about its environment, we use Docker containers for environment isolation. 

In the default configuration, all robot nodes are brought up in a single container with ``ros2 launch ad_r1m_robot bringup.launch.py``. Other containers may start up RMW servers (e.g. Zenoh daemon, DDS discovery) or extra application components of your choice.

Docker images should avoid hardware-specific variations as long as reasonable. All hardware differences should be handled by the previous system layer, and devices should be ultimately presented to the container in a hardware-agnostic manner (e.g. CAN adapter should be network interface ``can0`` regardless of adapter type).

A single Dockerfile unifies docker container builds for development with devcontainers, CI builds, CI testing, production builds, development ("tinkering") builds, etc. using Docker multi-stage builds.

.. mermaid::

    flowchart LR

    subgraph "3rd party images"
        $BASE_IMAGE[$BASE_IMAGE<br>$ROS_DISTRO-ros-base]
        ros-core[$ROS_DISTRO-ros-core]
    end

    $BASE_IMAGE --> common -- cache rosdeps --> depcacher
    common -- install build deps --> build_common -- install exec deps --> devcontainer
    build_common -- colcon build --> builder -- install exec deps --> dev

    builder -. built packages .-> runner

    ros-core --> runner

    subgraph "User-facing images"
        devcontainer
        dev
        runner
    end

Multiple containers are built from the same commit by changing the build args:

* ``ROS_DISTRO``
    * ``humble`` (default)
    * ``jazzy``
* ``FROM_IMAGE`` -- Image used as base for intermediary stages 
    * ``ros:$ROS_DISTRO`` (default)
* ``OVERLAY_WS`` -- Path inside container where to place ROS 2 overlay
    * ``/ros2_ws`` (default)
* ``BUILD_PACKAGES`` -- Space-separated list of (meta-)packages to include in build
    * ``ad_r1m_robot`` (default) -- Metapackage that depends on everything needed for a real robot
    * ``ad_r1m_sim`` -- Metapackage that depends on everything needed for a simulated robot
    * ...

The following combinations run in CI, as described in ``docker/dockers.yml``:

.. list-table::

    * - Docker tag
      - ``ROS_DISTRO``
      - ``BUILD_PACKAGES``
      - Supported architectures

    * - ``ad-r1m:sim-humble``
      - humble
      - ``ad_r1m_sim``
      - ``linux/amd64``

    * - ``ad-r1m:robot-humble``
      - humble
      - ``ad_r1m_robot``
      - ``linux/arm64``

    * - ``ad-r1m:robot-jazzy``
      - jazzy
      - ``ad_r1m_robot``
      - ``linux/arm64``
