Writing Your Own ROS 2 Nodes for AD-R1M
=======================================

.. contents:: Table of Contents
   :depth: 2
   :local:

This guide walks you through creating custom ROS 2 nodes for the AD-R1M robot platform, using the lift control service as a practical example.

Development Environment Setup
-----------------------------

Setting Up Your Workspace
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Access the development container**:

   .. code-block:: bash

      docker run -it \
        --network=host \
        --ipc=host \
        --pid=host \
        --privileged \
        -v /home/analog/ros_data:/ros_data \
        -e RMW_IMPLEMENTATION=rmw_zenoh_cpp \
        -e ROBOT_NAMESPACE=ad_r1m_0 \
        working bash

2. **Source the ROS 2 workspace**:

   .. code-block:: bash

      source /ros2_ws/install/setup.bash

3. **Create a new package** (for custom nodes):

   .. code-block:: bash

      cd /ros2_ws/src
      ros2 pkg create --build-type ament_python my_robot_nodes --dependencies rclpy std_msgs geometry_msgs

Package Structure
~~~~~~~~~~~~~~~~~

A typical ROS 2 Python package structure:

.. code-block:: text

   my_robot_nodes/
   ├── my_robot_nodes/
   │   ├── __init__.py
   │   ├── my_node.py
   │   └── my_service.py
   ├── resource/
   │   └── my_robot_nodes
   ├── test/
   ├── package.xml
   └── setup.py

Example: Creating a Lift Control Node
-------------------------------------

The AD-R1M includes a lift mechanism that can be controlled via ROS 2. This example demonstrates creating a service client and server for lift control.

Lift Service Definition
~~~~~~~~~~~~~~~~~~~~~~~

First, define the service interface. In the ``adrd_demo_ros2`` package, the lift service is defined as:

.. code-block:: text

   # LiftGPIO.srv
   int32 command
   ---
   bool success
   string message

Commands:

- ``0`` = Hold position
- ``1`` = Lift up
- ``2`` = Lift down

Lift Server Node (Python)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   Lift control server node for AD-R1M.
   Receives lift commands and controls GPIO.
   """
   import rclpy
   from rclpy.node import Node
   from adrd_demo_ros2.srv import LiftGPIO
   import RPi.GPIO as GPIO

   class LiftServer(Node):
       def __init__(self):
           super().__init__('lift_server')
           
           # GPIO setup
           self.lift_up_pin = 17
           self.lift_down_pin = 27
           GPIO.setmode(GPIO.BCM)
           GPIO.setup(self.lift_up_pin, GPIO.OUT)
           GPIO.setup(self.lift_down_pin, GPIO.OUT)
           
           # Create service
           self.srv = self.create_service(
               LiftGPIO, 
               '/elevator_to_robot', 
               self.lift_callback
           )
           
           self.get_logger().info('Lift server ready')

       def lift_callback(self, request, response):
           command = request.command
           
           if command == 0:  # Hold
               GPIO.output(self.lift_up_pin, GPIO.LOW)
               GPIO.output(self.lift_down_pin, GPIO.LOW)
               response.message = "Lift holding"
               
           elif command == 1:  # Up
               GPIO.output(self.lift_down_pin, GPIO.LOW)
               GPIO.output(self.lift_up_pin, GPIO.HIGH)
               response.message = "Lift going up"
               
           elif command == 2:  # Down
               GPIO.output(self.lift_up_pin, GPIO.LOW)
               GPIO.output(self.lift_down_pin, GPIO.HIGH)
               response.message = "Lift going down"
               
           else:
               response.success = False
               response.message = f"Unknown command: {command}"
               return response
           
           response.success = True
           self.get_logger().info(response.message)
           return response

       def destroy_node(self):
           GPIO.cleanup()
           super().destroy_node()

   def main():
       rclpy.init()
       node = LiftServer()
       try:
           rclpy.spin(node)
       except KeyboardInterrupt:
           pass
       finally:
           node.destroy_node()
           rclpy.shutdown()

   if __name__ == '__main__':
       main()

Lift Client Node (Python)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   Async lift control client for AD-R1M.
   """
   import rclpy
   from rclpy.node import Node
   from adrd_demo_ros2.srv import LiftGPIO

   class LiftClientAsync(Node):
       def __init__(self):
           super().__init__('lift_client')
           self.client = self.create_client(LiftGPIO, '/elevator_to_robot')
           
           while not self.client.wait_for_service(timeout_sec=1.0):
               self.get_logger().info('Waiting for lift service...')

       def send_command(self, command):
           """
           Send lift command asynchronously.
           
           Args:
               command: 0=hold, 1=up, 2=down
               
           Returns:
               Future object for the service call
           """
           request = LiftGPIO.Request()
           request.command = command
           return self.client.call_async(request)

   def main():
       rclpy.init()
       client = LiftClientAsync()
       
       # Example: Move lift up
       future = client.send_command(1)
       rclpy.spin_until_future_complete(client, future)
       
       result = future.result()
       print(f'Result: {result.success}, {result.message}')
       
       client.destroy_node()
       rclpy.shutdown()

   if __name__ == '__main__':
       main()

Creating a Publisher Node
-------------------------

Example: Custom Status Publisher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   Publishes custom robot status messages.
   """
   import rclpy
   from rclpy.node import Node
   from std_msgs.msg import String
   import json

   class StatusPublisher(Node):
       def __init__(self):
           super().__init__('status_publisher')
           
           self.publisher = self.create_publisher(String, '/robot_status', 10)
           self.timer = self.create_timer(1.0, self.publish_status)
           
           self.status = {
               'state': 'idle',
               'battery': 12.0,
               'errors': []
           }

       def publish_status(self):
           msg = String()
           msg.data = json.dumps(self.status)
           self.publisher.publish(msg)
           
       def update_state(self, new_state):
           self.status['state'] = new_state

   def main():
       rclpy.init()
       node = StatusPublisher()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

Creating a Subscriber Node
--------------------------

Example: Velocity Monitor
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   Monitors velocity commands and logs statistics.
   """
   import rclpy
   from rclpy.node import Node
   from geometry_msgs.msg import Twist
   import math

   class VelocityMonitor(Node):
       def __init__(self):
           super().__init__('velocity_monitor')
           
           self.subscription = self.create_subscription(
               Twist,
               '/cmd_vel',
               self.velocity_callback,
               10
           )
           
           self.max_linear = 0.0
           self.max_angular = 0.0
           
           self.timer = self.create_timer(5.0, self.report_stats)

       def velocity_callback(self, msg):
           linear = math.sqrt(msg.linear.x**2 + msg.linear.y**2)
           angular = abs(msg.angular.z)
           
           self.max_linear = max(self.max_linear, linear)
           self.max_angular = max(self.max_angular, angular)

       def report_stats(self):
           self.get_logger().info(
               f'Max velocities - Linear: {self.max_linear:.2f} m/s, '
               f'Angular: {self.max_angular:.2f} rad/s'
           )

   def main():
       rclpy.init()
       node = VelocityMonitor()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

Creating an Action Server
-------------------------

For long-running tasks, use ROS 2 actions.

Example: Dock Action Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   Action server for docking behavior.
   """
   import rclpy
   from rclpy.action import ActionServer
   from rclpy.node import Node
   from nav2_msgs.action import NavigateToPose
   from geometry_msgs.msg import Twist
   import time

   class DockActionServer(Node):
       def __init__(self):
           super().__init__('dock_action_server')
           
           self._action_server = ActionServer(
               self,
               NavigateToPose,
               'dock',
               self.execute_callback
           )
           
           self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

       async def execute_callback(self, goal_handle):
           self.get_logger().info('Executing docking...')
           
           feedback_msg = NavigateToPose.Feedback()
           
           # Simulate docking approach
           for i in range(10):
               if goal_handle.is_cancel_requested:
                   goal_handle.canceled()
                   return NavigateToPose.Result()
               
               # Move slowly forward
               cmd = Twist()
               cmd.linear.x = 0.1
               self.cmd_pub.publish(cmd)
               
               feedback_msg.distance_remaining = float(10 - i) / 10.0
               goal_handle.publish_feedback(feedback_msg)
               
               time.sleep(0.5)
           
           # Stop
           self.cmd_pub.publish(Twist())
           
           goal_handle.succeed()
           result = NavigateToPose.Result()
           return result

   def main():
       rclpy.init()
       node = DockActionServer()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

Integrating with Nav2
---------------------

Using the BasicNavigator
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """
   High-level navigation using Nav2's BasicNavigator.
   """
   from nav2_simple_commander.robot_navigator import BasicNavigator
   from geometry_msgs.msg import PoseStamped
   import rclpy

   def main():
       rclpy.init()
       navigator = BasicNavigator()
       
       # Wait for Nav2 to be ready
       navigator.waitUntilNav2Active()
       
       # Set initial pose
       initial_pose = PoseStamped()
       initial_pose.header.frame_id = 'map'
       initial_pose.pose.position.x = 0.0
       initial_pose.pose.position.y = 0.0
       initial_pose.pose.orientation.w = 1.0
       navigator.setInitialPose(initial_pose)
       
       # Navigate to goal
       goal_pose = PoseStamped()
       goal_pose.header.frame_id = 'map'
       goal_pose.pose.position.x = 2.0
       goal_pose.pose.position.y = 1.0
       goal_pose.pose.orientation.w = 1.0
       
       navigator.goToPose(goal_pose)
       
       while not navigator.isTaskComplete():
           feedback = navigator.getFeedback()
           print(f'Distance remaining: {feedback.distance_remaining:.2f}m')
       
       result = navigator.getResult()
       print(f'Navigation result: {result}')
       
       rclpy.shutdown()

   if __name__ == '__main__':
       main()

Building and Installing Your Package
------------------------------------

1. **Update setup.py** with your entry points:

   .. code-block:: python

      entry_points={
          'console_scripts': [
              'lift_server = my_robot_nodes.lift_server:main',
              'lift_client = my_robot_nodes.lift_client:main',
              'status_publisher = my_robot_nodes.status_publisher:main',
          ],
      },

2. **Build the package**:

   .. code-block:: bash

      cd /ros2_ws
      colcon build --packages-select my_robot_nodes
      source install/setup.bash

3. **Run your node**:

   .. code-block:: bash

      ros2 run my_robot_nodes lift_server

Creating a Launch File
----------------------

.. code-block:: python

   # launch/my_nodes.launch.py
   from launch import LaunchDescription
   from launch_ros.actions import Node

   def generate_launch_description():
       return LaunchDescription([
           Node(
               package='my_robot_nodes',
               executable='lift_server',
               name='lift_server',
               output='screen',
           ),
           Node(
               package='my_robot_nodes',
               executable='status_publisher',
               name='status_publisher',
               output='screen',
               parameters=[{
                   'publish_rate': 1.0,
               }],
           ),
       ])

Run with:

.. code-block:: bash

   ros2 launch my_robot_nodes my_nodes.launch.py

Best Practices
--------------

1. **Use namespaces** for multi-robot compatibility:

   .. code-block:: python

      self.create_publisher(Twist, 'cmd_vel', 10)  # Relative topic

2. **Handle exceptions** gracefully:

   .. code-block:: python

      try:
          rclpy.spin(node)
      except KeyboardInterrupt:
          pass
      finally:
          node.destroy_node()
          rclpy.shutdown()

3. **Use parameters** for configuration:

   .. code-block:: python

      self.declare_parameter('speed', 0.5)
      speed = self.get_parameter('speed').value

4. **Log appropriately**:

   .. code-block:: python

      self.get_logger().debug('Debug info')
      self.get_logger().info('Normal operation')
      self.get_logger().warn('Warning condition')
      self.get_logger().error('Error occurred')

5. **Test in isolation** before integrating with the full system
