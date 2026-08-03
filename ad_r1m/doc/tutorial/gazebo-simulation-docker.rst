.. _gazebo-simulation-docker:

AD-R1M Gazebo Simulation with Docker
====================================

Quickstart to run the AD-R1M Gazebo Classic simulation in a container on
Linux or Windows.

.. figure:: ../how-to/jetson/figures/simulation_demo.gif
   :align: center
   :width: 80%

.. contents:: Table of Contents
   :depth: 2
   :local:

Two paths:

* **Option A** — pull the nightly image from Cloudsmith (needs
  Cloudsmith access).
* **Option B** — build locally (~5–15 min).

Prerequisites — Linux (Ubuntu 22.04+)
-------------------------------------

.. code-block:: bash

   sudo apt update
   sudo apt install -y ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER

Log out and back in, then verify:

.. code-block:: bash

   docker buildx version

Prerequisites — Windows (WSL 2 + Ubuntu 22.04+)
-----------------------------------------------

Windows 11 required for WSLg (auto GUI forwarding). Any Ubuntu 22.04+
image works.

**1. Install WSL 2** — from PowerShell as Administrator:

.. code-block:: powershell

   wsl --install

Reboot when prompted; create a Linux username/password on first
launch.

**2. Open the WSL shell:**

.. code-block:: powershell

   wsl

**3. Enable systemd** — inside WSL:

.. code-block:: bash

   sudo tee /etc/wsl.conf > /dev/null <<'EOF'
   [boot]
   systemd=true
   EOF

Then from PowerShell:

.. code-block:: powershell

   wsl --shutdown

Reopen ``wsl``.

**4. Install Docker + Buildx** — same commands as the Linux section
above. Exit and re-enter ``wsl`` after ``usermod``, then verify:

.. code-block:: bash

   docker buildx version
   echo $DISPLAY          # :0
   ls /tmp/.X11-unix/     # X0

Option A — Pull the prebuilt image
----------------------------------

.. code-block:: bash

   docker login docker.cloudsmith.io
   docker pull docker.cloudsmith.io/adi/adrd-common/ad-r1m:sim-humble-nightly

Skip to :ref:`docker-sim-run`.

Option B — Build the image locally
----------------------------------

.. code-block:: bash

   git clone https://github.com/analogdevicesinc/ad-r1m-ros2.git
   cd ad-r1m-ros2
   docker buildx build . \
       -f docker/Dockerfile \
       --target dev \
       --build-arg BUILD_PACKAGES=ad_r1m_sim \
       -t ad-r1m:sim-humble-base

Add ``xterm`` as an overlay (the sim image doesn't ship it, and the
launch file's teleop node needs it):

.. code-block:: bash

   echo 'FROM ad-r1m:sim-humble-base' > docker/Dockerfile.xterm
   echo 'RUN apt-get update && apt-get install -y --no-install-recommends xterm && rm -rf /var/lib/apt/lists/*' >> docker/Dockerfile.xterm
   docker buildx build . \
       -f docker/Dockerfile.xterm \
       -t ad-r1m:sim-humble

.. tip::

   On Windows, clone under ``~/`` inside WSL — ``/mnt/c/`` is much
   slower for Docker I/O.

.. _docker-sim-run:

Run the simulation
------------------

.. code-block:: bash

   IMAGE=ad-r1m:sim-humble
   # or: IMAGE=docker.cloudsmith.io/adi/adrd-common/ad-r1m:sim-humble-nightly

On **native Linux only** (skip on WSL):

.. code-block:: bash

   xhost +local:docker

Launch:

.. code-block:: bash

   docker run --rm -it \
       -e DISPLAY \
       --net=host --ipc=host --pid=host \
       -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
       -v /dev/shm:/dev/shm \
       $IMAGE \
       ros2 launch ad_r1m_gazebo launch_sim.launch.py

Gazebo and RViz open. With the Option B xterm overlay, a keyboard
teleop window also opens:

.. code-block:: text

      u    i    o
      j    k    l
      m    ,    .

   q/z : increase/decrease max speeds by 10%
   CTRL-C to quit

Verify the ROS 2 graph
----------------------

In a second WSL/Linux terminal:

.. code-block:: bash

   docker run --rm -it --net=host --ipc=host --pid=host $IMAGE ros2 topic list
   docker run --rm -it --net=host --ipc=host --pid=host $IMAGE ros2 topic echo /odom --once

Troubleshooting
---------------

**Teleop errors with ``FileNotFoundError: 'xterm'``**
    Cloudsmith image lacks xterm. Run teleop directly in a second
    terminal — same remap the launch file uses:

    .. code-block:: bash

       docker run --rm -it \
           --net=host --ipc=host --pid=host \
           $IMAGE \
           ros2 run teleop_twist_keyboard teleop_twist_keyboard \
               --ros-args -r /cmd_vel:=cmd_vel_keyboard

**"BuildKit is enabled but the buildx component is missing"**
    Reinstall following the prerequisites — you have ``docker.io``, not
    ``docker-ce``.

**Gazebo windows don't appear (Windows/WSL)**
    ``wsl --update`` then ``wsl --shutdown`` from PowerShell. Confirm
    ``$DISPLAY`` and ``/tmp/.X11-unix/X0`` exist.

**"cannot open display" (Linux)**
    ``xhost +local:docker``.

**"unauthorized" pulling from Cloudsmith**
    ``docker login docker.cloudsmith.io`` — token must have access to
    ``adi/adrd-common``.

**Black or laggy Gazebo**
    Install `NVIDIA Container Toolkit
    <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>`__,
    add ``--gpus all`` to ``docker run``.

**Multiple containers can't see each other**
    All containers must use ``--net=host --ipc=host --pid=host``.

See also
--------

* :doc:`ros2-examples` — mapping, localization, Nav2 flows on the
  simulated robot.
* :doc:`../how-to/jetson/ad-r1m-realsense-gazebo` — Isaac Sim / Gazebo
  setup for Jetson AGX Orin (RealSense-integrated flow).
* :doc:`ros2-writing-your-own-nodes` — add custom nodes.
* `AD-R1M Dockerfile
  <https://github.com/analogdevicesinc/ad-r1m-ros2/blob/main/docker/Dockerfile>`__
* `Docker Engine on Ubuntu
  <https://docs.docker.com/engine/install/ubuntu/>`__
* `Install WSL <https://learn.microsoft.com/en-us/windows/wsl/install>`__
