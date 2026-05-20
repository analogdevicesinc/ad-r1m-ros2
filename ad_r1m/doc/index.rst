AD-R1M Robot Platform
=====================

.. figure:: figures/ad-r1m.png
   :align: right
   :alt: AD-R1M Robot Platform

   AD-R1M Open Mobile Robot Platform

The AD-R1M Open Mobile Robot Platform Reference Design is a modular, extensible, and fully open-source framework developed to accelerate the design, prototyping, and deployment of autonomous mobile robots.

This reference design integrates key hardware and software components, including motor control, sensor fusion, localization, navigation, and communication, into a cohesive platform that supports rapid development and experimentation.

Whether you're building a research prototype, an educational robot, or a commercial-grade autonomous system, this platform provides the flexibility and scalability needed to meet diverse application requirements. It is designed to be compatible with popular development tools, middleware (such as ROS 2), and embedded systems, making it ideal for both academic and industrial use.

.. clear-content:: both

In this documentation
---------------------

.. grid::
   :columns: 2

   .. card:: Tutorials
      :ref: tutorials

      **Get started** with hands-on introductions for the AD-R1M

   .. card:: How-to guides
      :ref: how-to-guides

      **Step-by-step guides** covering key operations and common tasks

   .. card:: Explanation
      :ref: explanation

      **Discussion and clarification** of key topics

   .. card:: Reference
      :ref: reference

      **Technical information**: specifications, APIs, architecture


Applications showcase
---------------------

SLAM
^^^^

.. image:: figures/do_mapping.gif
  :width: 600px

Navigation
^^^^^^^^^^

.. image:: figures/navigate.gif
  :width: 600px

Multi-robot fleet
^^^^^^^^^^^^^^^^^

.. image:: figures/amr_multi_robot.gif
  :width: 600px

Nvidia cuVSLAM
^^^^^^^^^^^^^^

.. image:: figures/ad_r1m_and_cuvslam_demo.gif
  :width: 600px

GMSL Camera integration and image processing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Floor segmentation
''''''''''''''''''

.. image:: figures/segmentation_result.gif
  :width: 600px

Object Detection
''''''''''''''''

.. image:: figures/detection_result.gif
  :width: 600px

Features
--------

- Open-source hardware and software design
- Support for ROS 2 Humble, Jazzy
- Differential drive mobile base with encoder feedback
- Support for NVIDIA Jetson AGX Orin for GPU-accelerated workloads
- Gazebo simulation environment included

Components
----------

.. flex::
   :class: centered

   .. card:: Wide Dynamic Range, six axis IMU

      :adi:`ADIS16470`
  
   .. card:: Front-facing ToF camera

      :adi:`EVAL-ADTF3175D-NXZ`

   .. card:: FOC motor drives

      :adi:`ADRD3161-01Z`

   .. card:: Robotics carrier for Raspberry Pi

      :adi:`ADRD4161-01Z`
   
   .. card:: 3S Li-ion battery pack and BMS

      :adi:`ADRD5161-01Z`

Applications
------------

- Mobile robotics research and development
- Autonomous navigation and SLAM algorithm development
- Warehouse and logistics automation prototyping
- Educational robotics platforms
- Multi-robot setup management research

System Architecture
-------------------

The AD-R1M platform consists of the following major subsystems:

- **Processing Unit**: Raspberry Pi 5 (base) or NVIDIA Jetson AGX Orin (advanced)
- **Motion Control**: Dual ADRD3161 motor driver boards with CAN interface
- **Power Management**: ADRD5161 BMS board (3S or 12S battery variants)
- **Sensors**: ADIS16470 IMU, ADTF3175D ToF camera, optional Intel RealSense
- **Connectivity**: CAN bus, USB, Ethernet, Wi-Fi, CRSF radio

Repository
----------

* GitHub: `ad-r1m-ros2 <https://github.com/analogdevicesinc/ad-r1m-ros2>`_
* ROS2 Packages: See the `package list <https://github.com/analogdevicesinc/ad-r1m-ros2#readme>`_

Help and Support
----------------

For questions and technical support, please visit the `EngineerZone <https://ez.analog.com/>`__ community forum.

.. toctree::
   :hidden:
   :includehidden:
   :titlesonly:

   tutorial/index
   how-to/index
   reference/index
   explanation/index
