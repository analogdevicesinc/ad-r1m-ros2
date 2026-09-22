NVIDIA\ |reg| Jetson\ |tm| AGX Orin and NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM Integration
========================================

This section covers integration of the AD-R1M robot with NVIDIA Jetson AGX Orin
and Isaac\ |tm| ROS Visual SLAM for advanced localization and mapping capabilities.

Overview
--------

The NVIDIA Jetson AGX Orin integration extends the AD-R1M platform with GPU-accelerated
visual SLAM capabilities using Isaac ROS Visual SLAM. This enables:

- Real-time visual-inertial odometry
- GPU-accelerated point cloud processing
- Enhanced localization accuracy
- Integration with Nav2 navigation stack

Requirements
------------

- NVIDIA\ |reg| Jetson\ |tm| AGX Orin Developer Kit
- NVIDIA\ |reg| JetPack\ |tm| 6.2.1 or later
- Intel\ |reg| RealSense\ |tm| D455 Camera
- AD-R1M Robot Platform

Getting Started
---------------

Follow the setup guides in order:

.. toctree::
   :titlesonly:

   agx-orin-setup
   setup-req-pkg-agx-orin
   setup-isaac-ros-agx-orin
   setup-isaac-ros-vslam
   vslam-setup-and-usage
   ad-r1m-jetson-orin-hardware-setup
   ad-r1m-cuvslam-setup
   ad-r1m-and-nvidia-cuvslam
   map-building-for-nav2
   ad-r1m-realsense-gazebo

