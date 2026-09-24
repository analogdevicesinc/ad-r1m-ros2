AD-R1M Specifications
=====================

This document provides an overview of the AD-R1M's components, capabilities, and design parameters.

Hardware components
-------------------

The base AD-R1M variant consists of:

- 1x Raspberry Pi 5 -- **main compute**
- 1x :adi:`ADRD4161-01Z` robotics connectivity carrier for rpi, providing connectivity options for: ADIS IMUs, CAN bus, GPIOs
- 1x :adi:`ADIS16470` IMU
- 1x :adi:`EVAL-ADTF3175` ToF camera
- 1x :adi:`ADRD5161-01Z` BMS module, on a LiPo 3S2P battery pack
- 2x :adi:`ADRD3161-01Z` motor drive modules
- 2x :adi:`QSH5718-51-28-101-10K <qsh5718>` stepper motors with high resolution encoders

Hardware add-ons
^^^^^^^^^^^^^^^^

The AD-R1M supports connecting extra hardware for enhanced function, via:

- Wired 1Gbps Ethernet -- for other compute platforms with network
- 1x USB 3.0, 2x USB 2.0 ports available on the Pi
- GPIOs, broken out on the carrier board

We provide reference designs for the following add-on hardware combinations:

- NVIDIA\ |reg| Jetson\ |tm| AGX Orin + one or more Intel\ |reg| RealSense\ |tm| stereo cameras
- NVIDIA\ |reg| Jetson\ |tm| Xavier NX + :adi:`AD-GMSL522-SL` GMSL\ |tm| Carrier Board + 4x GMSL\ |tm| cameras

Software stack
--------------

The **Raspberry Pi 5 main compute** platform powering the robot runs a software stack composed of:

- ADI Kuiper Linux, ADI's Debian-based distribution
- Docker
- ROS 2 Humble

The default robot runtime has ROS 2 functionalities for:

- Motion control
- Full robot sensing: motor feedback, IMU, cameras
- Sensor fusion
- Manual teleoperation
- Autonomous operation: SLAM, navigation

The robotics modules on board run open source Zephyr\ |reg| firmware and communicate via CAN bus using the CANopen\ |reg| protocol stack and appropriate CiA\ |reg| DSPs:

- `ADRD3161 firmware <https://github.com/analogdevicesinc/adrd3161-fw>`__ implements a CiA\ |reg| 402 device
- `ADRD4161 firmware <https://github.com/analogdevicesinc/adrd4161-fw>`__ implements a slcan adapter
- `ADRD5161 firmware <https://github.com/analogdevicesinc/adrd5161-fw>`__ implements a CiA\ |reg| 419 device

Mechanical specifications
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Construction
     - T-slot Aluminium extrusion, metric 20-series
     - 
   * - Dimensions (L x W x H)
     - 585 x 360 x 150 mm
     - Chassis only, without payload
   * - Weight
     - ~ 10 kg
     - Base configuration, battery included
   * - Payload capacity
     - N/A
     - Not rated for payload carrying. Capacity heavily influenced by drive surface, tunable motor soft limits

Drive system specifications
---------------------------
.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Kinematics
     - Differential drive
     - 2 driven wheels on left-right axis through geometric center
   * - Drive wheel diameter
     - 100 mm
     - Not including wear, dynamic deformation
   * - Drive wheel width
     - 25 mm
     - Not including wear, dynamic deformation
   * - Drive wheel track (base width)
     - 220 mm
     - Wheel contact patch center-to-center
   * - Caster wheel diameter
     - 50 mm
     - 4x caster wheels
   * - Caster wheel ground clearance
     - ~ 5 mm
     - Drive wheels maintain ground contact; Robot slightly swings around drive wheel axis
   * - Motor current limit
     - 2.5 A
     - Per motor. Soft limit. Default tuning parameters; may be tuned up.
   * - Max speed
     - 2.0 m/s
     - Soft limited by default motor tuning parameter set. Near system limit; needs HW upgrade to be significantly increased.
   * - Default speed
     - 1.0 m/s
     - Controlled by ROS 2 teleop and nav2 configs

Battery power specifications
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - Battery cell
     - NCR18650GA
     - 
   * - Battery configuration
     - 3S2P (3 series pairs of 2 parallel cells each)
     -
   * - Battery voltage
     - 9.0 - 12.6 V
     - Range
   * - Battery voltage
     - 10.8 V (3 x 3.6 V)
     - Nominal
   * - Battery capacity
     - 6600 mAh (2 x 3300 mAh)
     - Nominal
   * - Charge time
     - 2 h
     - Robot powered on but idle.
   * - Operating time
     - 2 - 3 h
     - Constant motion on soft terrain (e.g. soft rubber, carpet)
   * - Operating time
     - 12 h
     - Motors idle

Sensor specifications
---------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - ToF camera range
     - 0.4 - 4.0 m
     -
   * - ToF camera FOV
     - 75\ |deg| horizontal / 90\ |deg| diagonal
     -
   * - ToF camera resolution
     - 512 x 512 px
     - Each pixel has: one depth value (mm from sensor origin), one infrared albedo value
   * - IMU sampling frequency
     - 200 Hz (default) / 2000 Hz (max)
     - Configurable via libIIO

Electrical specifications
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Parameter
     - Value
     - Notes
   * - CAN Bus Speed
     - 500 kbps
     -
