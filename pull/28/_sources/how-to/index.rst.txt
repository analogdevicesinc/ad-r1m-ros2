.. _how-to-guides:

How-to guides
=============

The following pages are step-by-step guides for accomplishing specific tasks.

Robot applications
------------------

Instructions for running various AD-R1M application-level activities, starting from a working base system:

.. toctree::
   :titlesonly:

   AD-R1M use-cases <use-cases>
   Troubleshooting <troubleshooting>


Setup guides
------------

Instructions for setting up various hardware/software configurations directly on the AD-R1M, or for connected devices.

Base AD-R1M (Raspberry Pi 5)
''''''''''''''''''''''''''''

.. toctree::
   :titlesonly:

   Build an AD-R1M from scratch <build-from-scratch/index>

AD-R1M + NVIDIA\ |reg| Jetson\ |tm| AGX Orin
''''''''''''''''''''''''''''''''''''''''''''

The NVIDIA Jetson AGX Orin integration adds NVIDIA Isaac\ |tm| ROS Visual SLAM capabilities for advanced visual-inertial odometry and enhanced navigation performance.

.. figure:: ../how-to/jetson/figures/simulation_demo.gif
   :align: center
   :width: 80%

   AD-R1M with Isaac ROS Visual SLAM in Gazebo simulation

For complete NVIDIA Jetson AGX Orin setup and Isaac ROS integration instructions, see:

.. toctree::
   :titlesonly:

   jetson/index
