AD-R1M Specifications
=====================

Software & Middleware
^^^^^^^^^^^^^^^^^^^^^

- **ROS 2 Enabled** for:

  - Navigation
  - Motion Control
  - Sensor Integration
  - Battery Management

- **Modular ROS 2 Nodes** for:

  - Localization
  - Navigation
  - Motion
  - BMS

- Compatible with **ROS 2 Humble** Distribution
- **Zephyr Support** for embedded firmware on motor, navigation, and BMS boards
- **CAN** communication between platforms

Hardware Components
^^^^^^^^^^^^^^^^^^^

**Processing Units**

- Raspberry Pi 5 (with ADI Kuiper2)
- NVIDIA Jetson AGX Orin

**Motor & Motion Control**

- Motor Drivers with Encoder Feedback
- Motor Control Board with Zephyr Firmware

**Power Management**

- Battery Management System board variants (BMS):

  - 3S BMS with Zephyr Firmware, or
  - 12S BMS with Zephyr Firmware

- Power Management for Mobile Operation

**Sensor Suite**

- ADI IMU (ADIS16470) for Localization
- ADI Time-of-Flight Camera (ADTF3175D) for Perception
- Intel RealSense Camera (optional)

**Connectivity**

- USB-to-CAN Adapter
- Ethernet and Wi-Fi Interfaces

Mechanical Specifications
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Dimensions (L × W × H)
     - 585 mm × 360 mm × 150 mm
     - Chassis only, without payload
   * - Weight (base configuration)
     - ~10 kg
     - With battery (chassis mass)
   * - Payload Capacity
     - TBD kg
     - Maximum recommended
   * - Wheel Diameter
     - 100 mm
     - Drive wheels
   * - Wheel Width
     - 25 mm
     - Drive wheels
   * - Wheel Track (Base Width)
     - 220 mm
     - Center-to-center
   * - Caster Wheel Diameter
     - 50 mm
     - 4× caster wheels
   * - Ground Clearance
     - 30 mm
     - At caster wheels

Electrical Specifications
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Battery Voltage
     - 11.1V (3S) / 44.4V (12S)
     - Nominal
   * - Battery Capacity
     - TBD Ah
     -
   * - Operating Time
     - TBD hours
     - Typical use
   * - Motor Power
     - TBD W
     - Per motor
   * - CAN Bus Speed
     - 500 kbps
     -

Performance Specifications
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Maximum Speed
     - TBD m/s
     - Configurable via ROS 2 velocity smoother nodes
   * - Maximum Angular Velocity
     - TBD rad/s
     - Configurable via ROS 2 velocity smoother nodes
   * - Localization Accuracy
     - TBD cm
     - With IMU + wheel odometry
   * - ToF Camera Range
     - 0.4 - 5.0 m
     - ADTF3175D
   * - ToF Camera FOV
     - 75° horizontal
     - ±37.5° (0.654 rad)
   * - ToF Camera Resolution
     - 512 × 512 px
     - Depth image
   * - IMU Sampling Frequency
     - 200 Hz (default) / 2000 Hz (max)
     - ADIS16470 configurable via IIO
   * - IMU Dimensions
     - 15 × 10 × 10 mm
     - ADIS16470 module

