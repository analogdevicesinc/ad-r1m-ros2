AD-R1M Use Case Examples
========================

.. contents:: Table of Contents
   :depth: 2
   :local:

This page provides practical use case examples for the AD-R1M robot platform.

.. seealso::

   For mapping, localization, and navigation tutorials, see :doc:`software-guide/ros2-examples`.

IMU Data Logging
----------------

Capture and log IMU data for analysis, calibration, or offline processing.

Real-Time IMU Recording
~~~~~~~~~~~~~~~~~~~~~~~

Record IMU data to a ROS2 bag file:

.. code-block:: bash

   # Start recording IMU data
   ros2 bag record /imu -o imu_recording

   # Record with timestamp in filename
   ros2 bag record /imu -o imu_$(date +%Y%m%d_%H%M%S)

   # Record multiple topics
   ros2 bag record /imu /odom /cam1/scan -o sensor_data

Playback and Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List bag contents
   ros2 bag info imu_recording

   # Playback bag file
   ros2 bag play imu_recording

   # Playback at slower speed for analysis
   ros2 bag play imu_recording --rate 0.5

Python IMU Analysis Script
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import Imu
   import csv

   class ImuLogger(Node):
       def __init__(self):
           super().__init__('imu_logger')
           self.subscription = self.create_subscription(
               Imu, '/imu', self.imu_callback, 10)
           self.csv_file = open('imu_data.csv', 'w', newline='')
           self.writer = csv.writer(self.csv_file)
           self.writer.writerow(['timestamp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'])

       def imu_callback(self, msg):
           self.writer.writerow([
               msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
               msg.linear_acceleration.x,
               msg.linear_acceleration.y,
               msg.linear_acceleration.z,
               msg.angular_velocity.x,
               msg.angular_velocity.y,
               msg.angular_velocity.z
           ])

   def main():
       rclpy.init()
       node = ImuLogger()
       try:
           rclpy.spin(node)
       finally:
           node.csv_file.close()
           node.destroy_node()
           rclpy.shutdown()

Multi-Camera Recording Setup
----------------------------

Configure and record from multiple camera sources for perception development.

Recording ToF Camera Data
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Record depth images
   ros2 bag record /cam1/depth_image /cam1/camera_info -o tof_recording

   # Record with compression
   ros2 bag record /cam1/depth_image --compression-mode file -o tof_compressed

Recording LaserScan Data
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Record converted laser scan
   ros2 bag record /cam1/scan -o laserscan_recording

   # Record all camera-related topics
   ros2 bag record /cam1/depth_image /cam1/scan /cam1/camera_info -o camera_full

Multi-Sensor Synchronized Recording
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Record all sensor data for full system capture
   ros2 bag record \
       /imu \
       /cam1/depth_image \
       /cam1/scan \
       /cam1/camera_info \
       /odom \
       /tf \
       /tf_static \
       -o full_sensor_recording

Autonomous Patrol Mission
-------------------------

Create a patrol mission where the robot visits multiple waypoints repeatedly.

Patrol Script Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   import rclpy
   from rclpy.node import Node
   from nav2_simple_commander.robot_navigator import BasicNavigator
   from geometry_msgs.msg import PoseStamped
   import time

   class PatrolMission(Node):
       def __init__(self):
           super().__init__('patrol_mission')
           self.navigator = BasicNavigator()
           
           # Define patrol waypoints
           self.waypoints = [
               self.create_pose(1.0, 0.0, 0.0),
               self.create_pose(2.0, 1.0, 1.57),
               self.create_pose(1.0, 2.0, 3.14),
               self.create_pose(0.0, 1.0, -1.57),
           ]
           
       def create_pose(self, x, y, yaw):
           pose = PoseStamped()
           pose.header.frame_id = 'map'
           pose.header.stamp = self.get_clock().now().to_msg()
           pose.pose.position.x = x
           pose.pose.position.y = y
           pose.pose.orientation.z = math.sin(yaw / 2)
           pose.pose.orientation.w = math.cos(yaw / 2)
           return pose

       def run_patrol(self, num_loops=3):
           self.navigator.waitUntilNav2Active()
           
           for loop in range(num_loops):
               self.get_logger().info(f'Starting patrol loop {loop + 1}/{num_loops}')
               
               for i, waypoint in enumerate(self.waypoints):
                   waypoint.header.stamp = self.get_clock().now().to_msg()
                   self.navigator.goToPose(waypoint)
                   
                   while not self.navigator.isTaskComplete():
                       feedback = self.navigator.getFeedback()
                       time.sleep(0.5)
                   
                   result = self.navigator.getResult()
                   self.get_logger().info(f'Waypoint {i+1} reached: {result}')
               
               self.get_logger().info(f'Patrol loop {loop + 1} complete')

   def main():
       rclpy.init()
       import math
       patrol = PatrolMission()
       patrol.run_patrol(num_loops=5)
       patrol.destroy_node()
       rclpy.shutdown()

   if __name__ == '__main__':
       main()

Object Tracking and Following
-----------------------------

Implement a simple follow behavior using sensor data.

Follow Point Example
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import LaserScan
   from geometry_msgs.msg import Twist
   import math

   class FollowClosest(Node):
       def __init__(self):
           super().__init__('follow_closest')
           self.subscription = self.create_subscription(
               LaserScan, '/cam1/scan', self.scan_callback, 10)
           self.publisher = self.create_publisher(Twist, '/cmd_vel_nav', 10)
           
           self.target_distance = 1.0  # meters
           self.kp_linear = 0.5
           self.kp_angular = 1.0

       def scan_callback(self, msg):
           # Find closest point
           min_range = float('inf')
           min_angle = 0
           
           for i, r in enumerate(msg.ranges):
               if msg.range_min < r < msg.range_max:
                   if r < min_range:
                       min_range = r
                       min_angle = msg.angle_min + i * msg.angle_increment
           
           if min_range < float('inf'):
               cmd = Twist()
               
               # Linear velocity: move toward target distance
               distance_error = min_range - self.target_distance
               cmd.linear.x = self.kp_linear * distance_error
               cmd.linear.x = max(-0.3, min(0.3, cmd.linear.x))
               
               # Angular velocity: turn toward closest point
               cmd.angular.z = -self.kp_angular * min_angle
               cmd.angular.z = max(-0.5, min(0.5, cmd.angular.z))
               
               self.publisher.publish(cmd)

   def main():
       rclpy.init()
       node = FollowClosest()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

Odometry Evaluation
-------------------

Compare wheel odometry with fused odometry to evaluate sensor fusion performance.

Odometry Comparison Script
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   import rclpy
   from rclpy.node import Node
   from nav_msgs.msg import Odometry
   import math

   class OdometryComparator(Node):
       def __init__(self):
           super().__init__('odom_comparator')
           
           self.wheel_odom = None
           self.fused_odom = None
           
           self.sub_wheel = self.create_subscription(
               Odometry, '/diff_drive_controller/odom', 
               self.wheel_callback, 10)
           self.sub_fused = self.create_subscription(
               Odometry, '/odometry/filtered', 
               self.fused_callback, 10)
           
           self.timer = self.create_timer(1.0, self.compare_callback)

       def wheel_callback(self, msg):
           self.wheel_odom = msg

       def fused_callback(self, msg):
           self.fused_odom = msg

       def compare_callback(self):
           if self.wheel_odom and self.fused_odom:
               dx = self.fused_odom.pose.pose.position.x - self.wheel_odom.pose.pose.position.x
               dy = self.fused_odom.pose.pose.position.y - self.wheel_odom.pose.pose.position.y
               distance_error = math.sqrt(dx*dx + dy*dy)
               
               self.get_logger().info(
                   f'Position difference: {distance_error:.3f}m '
                   f'(dx={dx:.3f}, dy={dy:.3f})')

   def main():
       rclpy.init()
       node = OdometryComparator()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

Low-Level Motor Control (Without ROS2)
--------------------------------------

For direct motor control without the ROS2 stack, use Python CANopen.

Python CANopen Example
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import canopen
   from canopen.profiles.p402 import BaseNode402
   import time

   # Initialize motor node
   node = BaseNode402(0x16, 'ardagvmotor.eds')
   network = canopen.Network()
   network.connect(channel='can0', interface='socketcan', bitrate=500000)
   network.add_node(node)

   # Start sync messages
   network.sync.start(0.1)

   # Configure node
   node.nmt.state = 'RESET'
   node.nmt.wait_for_bootup(5)
   node.load_configuration()
   node.setup_402_state_machine()
   node.nmt.state = 'OPERATIONAL'

   def set_speed(v):
       """Set motor speed. v = -1 to 1"""
       v = int(v * 4000000)  # Convert to internal units
       node.rpdo[4]['Controlword'].raw = 0b1111
       node.rpdo[4]['Target velocity'].raw = v
       node.rpdo[4].transmit()

   # Enable motors
   node.state = 'OPERATION ENABLED'

   # Test motion
   set_speed(0.5)
   time.sleep(1)
   set_speed(-0.5)
   time.sleep(1)
   set_speed(0)

   # Disable motors
   node.state = 'SWITCH ON DISABLED'

Battery Monitoring Application
------------------------------

Monitor battery status and implement low-battery behavior.

Battery Monitor Node
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   import rclpy
   from rclpy.node import Node
   from std_msgs.msg import Float32
   from geometry_msgs.msg import Twist

   class BatteryMonitor(Node):
       def __init__(self):
           super().__init__('battery_monitor')
           
           self.battery_voltage = 12.0
           self.low_voltage_threshold = 10.0
           self.critical_voltage_threshold = 9.0
           
           # Subscribe to battery voltage (from CRSF telemetry)
           self.sub = self.create_subscription(
               Float32, '/battery_voltage', self.battery_callback, 10)
           
           # Publisher to stop robot in emergency
           self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
           
           self.timer = self.create_timer(5.0, self.check_battery)

       def battery_callback(self, msg):
           self.battery_voltage = msg.data

       def check_battery(self):
           if self.battery_voltage < self.critical_voltage_threshold:
               self.get_logger().error(
                   f'CRITICAL: Battery at {self.battery_voltage}V! Stopping robot.')
               self.stop_robot()
           elif self.battery_voltage < self.low_voltage_threshold:
               self.get_logger().warn(
                   f'LOW BATTERY: {self.battery_voltage}V. Return to charger soon.')
           else:
               self.get_logger().info(f'Battery: {self.battery_voltage}V')

       def stop_robot(self):
           cmd = Twist()
           cmd.linear.x = 0.0
           cmd.angular.z = 0.0
           self.cmd_pub.publish(cmd)

   def main():
       rclpy.init()
       node = BatteryMonitor()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()
