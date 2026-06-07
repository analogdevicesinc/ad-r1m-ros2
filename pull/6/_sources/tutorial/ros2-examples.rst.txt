AD-R1M ROS2 Examples
====================

.. contents:: Table of Contents
   :depth: 2
   :local:

This page provides practical examples for using the AD-R1M robot with ROS2, including mapping, localization, and autonomous navigation.

.. _mapping-with-slam:

Mapping with SLAM Toolbox
-------------------------

Create a map of your environment using SLAM Toolbox for real-time mapping.

Starting the Mapping Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # On the robot (via SSH)
   ~/bringup_mapping.sh

**Active Docker Compose Services**:

- ``motors``, ``imu``, ``tof``, ``tof_republish`` (core sensors/actuators)
- ``mapping`` (SLAM Toolbox)
- ``teleop_radio`` (radio control for driving)
- ``rmw_zenoh_router`` (middleware)

Mapping Process
~~~~~~~~~~~~~~~

1. **Start RViz** on your host computer (see :doc:`ros2-getting-started`):

   .. code-block:: bash

      cd platform/common/scripts
      ./start_rviz.sh 0 false

2. **Change the Fixed Frame** in RViz to ``map``

3. **Arm the robot** using the killswitch on the RC handset (switch SA to "ARMED")

4. **Drive the robot around** using the right stick on the remote control

.. figure:: ../figures/do_mapping.png
   :alt: Mapping in RViz
   :align: center
   :width: 800px

   RViz mapping view - change Fixed Frame to "map"

.. figure:: ../figures/do_mapping.gif
   :align: center
   :width: 800px
   
   Robot mapping demonstration

**Map Legend:**

- **White areas** = Free space (safe to navigate)
- **Black areas** = Obstacles (walls, objects)
- **Gray areas** = Unexplored/unknown

Saving the Map
~~~~~~~~~~~~~~

After mapping is complete, save the map:

.. code-block:: bash

   # Use the convenience script
   ~/save_map.sh

   # Or manually
   ros2 run nav2_map_server map_saver_cli -f /ros_data/maps/map

This creates two files in ``/home/analog/ros_data/maps/``:

- ``map.pgm`` - Grayscale image (white=free, black=occupied, gray=unknown)
- ``map.yaml`` - Map metadata (resolution, origin, thresholds)

SLAM Configuration
~~~~~~~~~~~~~~~~~~

SLAM Toolbox parameters: ``/ros_data/mapping_params.yaml``

Key parameters:

.. code-block:: yaml

   slam_toolbox:
     ros__parameters:
       resolution: 0.05            # Map resolution (meters/pixel)
       max_laser_range: 5.0        # Maximum laser range to use
       minimum_travel_distance: 0.3  # Min distance before adding scan

Localization with AMCL
----------------------

Once you have a map, use AMCL (Adaptive Monte Carlo Localization) to localize the robot.

Starting Localization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start with AMCL localization and Nav2
   ~/bringup_amcl.sh

   # Or with explicit environment variables
   LOCALIZATION=amcl NAVIGATION=nav2 TELEOP=radio ~/bringup.sh

Setting Initial Pose
~~~~~~~~~~~~~~~~~~~~

In RViz:

1. Click **2D Pose Estimate** in the toolbar
2. Click on the map where the robot is located
3. Drag to set the orientation (direction robot is facing)

.. figure:: ../figures/locate.gif
   :align: center
   :width: 800px

   Setting initial pose for AMCL localization

The robot's estimated position (red arrow) and uncertainty (purple ellipse) will be displayed.

**Tips for good localization:**

- Set the initial pose as accurately as possible
- Drive the robot around to help particles converge
- Ensure the saved map matches the current environment

AMCL Topics
~~~~~~~~~~~

- Publishes: ``/amcl_pose`` (geometry_msgs/PoseWithCovarianceStamped)
- Publishes: TF transform (``map`` → ``odom``)
- Subscribes: ``/cam1/scan`` (laser scan)
- Subscribes: ``/odom`` (odometry)

.. _autonomous-navigation:

Autonomous Navigation with Nav2
-------------------------------

Use the Nav2 navigation stack for autonomous point-to-point navigation.

Starting Navigation
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start full navigation stack
   ~/bringup_amcl.sh

**Note**: ``bringup_amcl.sh`` enables both AMCL localization and Nav2 navigation.

Sending Navigation Goals
~~~~~~~~~~~~~~~~~~~~~~~~

In RViz:

1. Click **2D Nav Goal** in the toolbar
2. Click on the desired destination on the map
3. Drag to set the goal orientation
4. The robot will plan a path and navigate autonomously

.. figure:: ../figures/nav_view.png
   :alt: Navigation View
   :align: center
   :width: 800px

   RViz navigation view showing global path and costmaps

.. figure:: ../figures/navigate.gif
   :align: center
   :width: 800px
   
   Robot autonomous navigation demonstration

**Navigation displays:**

- **Green line** - Global path plan
- **Colored regions** - Costmap (inflation around obstacles)
- **Robot footprint** - Current robot position

Navigation Topics
~~~~~~~~~~~~~~~~~

- Subscribes: ``/goal_pose`` (geometry_msgs/PoseStamped)
- Publishes: ``/cmd_vel_nav`` (velocity commands to twist_mux)
- Publishes: ``/plan`` (global path)
- Publishes: ``/local_costmap/costmap``, ``/global_costmap/costmap``

Nav2 Configuration
~~~~~~~~~~~~~~~~~~

Navigation parameters: ``/ros_data/navigation_params.yaml``

Key parameters:

.. code-block:: yaml

   controller_server:
     ros__parameters:
       controller_frequency: 20.0
       FollowPath:
         max_vel_x: 0.5          # Maximum forward velocity
         max_vel_theta: 1.0      # Maximum angular velocity
         xy_goal_tolerance: 0.1  # Position tolerance at goal
         yaw_goal_tolerance: 0.1 # Orientation tolerance at goal

For detailed navigation tuning, see the `Nav2 documentation <https://docs.nav2.org/>`__.

ROS 2 Topics Reference
----------------------

Core sensor and control topics used by the AD-R1M:

**Sensor Data**

- ``/cam1/scan`` - 2D laser scan (from ToF depth-to-laserscan)
- ``/cam1/depth_image`` - Raw depth image from ToF camera
- ``/imu`` - IMU data (angular velocities, linear accelerations)

**Odometry and Localization**

- ``/diff_drive_controller/odom`` - Raw odometry from wheel encoders
- ``/odom`` - Fused odometry (encoder + IMU via EKF)
- ``/amcl_pose`` - AMCL localization pose estimate

**Motion Control**

- ``/cmd_vel_joy`` - Velocity commands from RC handset
- ``/cmd_vel_nav`` - Velocity commands from Nav2
- ``/diff_drive_controller/cmd_vel_unstamped`` - Final commands to motors

**Navigation**

- ``/goal_pose`` - Navigation goals
- ``/plan`` - Global path
- ``/map`` - Occupancy grid map

.. code-block:: bash

   # List all active topics
   ros2 topic list

   # Echo a topic
   ros2 topic echo /imu --once

   # Check topic frequency
   ros2 topic hz /cam1/scan

For detailed architecture information, see :doc:`/explanation/ros2-architecture`.

.. code-block:: xml

   <root main_tree_to_execute="MainTree">
     <BehaviorTree ID="MainTree">
       <Sequence name="navigate_sequence">
         <ComputePathToPose goal="{goal}" path="{path}" planner_id="GridBased"/>
         <FollowPath path="{path}" controller_id="FollowPath"/>
       </Sequence>
     </BehaviorTree>
   </root>

Load custom behavior trees via the Nav2 parameters:

.. code-block:: yaml

   bt_navigator:
     ros__parameters:
       default_bt_xml_filename: "/path/to/custom_bt.xml"

Waypoint Following
------------------

For multi-waypoint missions, use the waypoint follower action.

Python Waypoint Example
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from nav2_simple_commander.robot_navigator import BasicNavigator
   from geometry_msgs.msg import PoseStamped

   navigator = BasicNavigator()

   # Define waypoints
   waypoints = []
   
   waypoint1 = PoseStamped()
   waypoint1.header.frame_id = 'map'
   waypoint1.pose.position.x = 1.0
   waypoint1.pose.position.y = 0.0
   waypoint1.pose.orientation.w = 1.0
   waypoints.append(waypoint1)

   waypoint2 = PoseStamped()
   waypoint2.header.frame_id = 'map'
   waypoint2.pose.position.x = 2.0
   waypoint2.pose.position.y = 1.0
   waypoint2.pose.orientation.w = 1.0
   waypoints.append(waypoint2)

   # Start waypoint following
   navigator.followWaypoints(waypoints)

   while not navigator.isTaskComplete():
       feedback = navigator.getFeedback()
       print(f'Current waypoint: {feedback.current_waypoint}')

   result = navigator.getResult()
   print(f'Navigation result: {result}')

Command Line Waypoint Navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send a single goal via command line:

.. code-block:: bash

   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
     "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"

Nav2 Custom Actions
-------------------

Create custom Nav2 action plugins for specialized behaviors.

Custom Action Plugin Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: cpp

   #include "nav2_behavior_tree/bt_action_node.hpp"

   class MyCustomAction : public nav2_behavior_tree::BtActionNode<my_msgs::action::MyAction>
   {
   public:
     MyCustomAction(
       const std::string & xml_tag_name,
       const std::string & action_name,
       const BT::NodeConfiguration & conf)
     : BtActionNode<my_msgs::action::MyAction>(xml_tag_name, action_name, conf)
     {}

     void on_tick() override
     {
       // Set action goal
       goal_.target = getInput<double>("target").value();
     }

     BT::NodeStatus on_success() override
     {
       return BT::NodeStatus::SUCCESS;
     }
   };

Register the plugin in your package's CMakeLists.txt and plugin XML.

Lift Control Integration
~~~~~~~~~~~~~~~~~~~~~~~~

The AD-R1M includes a lift mechanism controlled via ROS2 services:

.. code-block:: python

   import rclpy
   from rclpy.node import Node
   from adrd_demo_ros2.srv import LiftGPIO

   class LiftController(Node):
       def __init__(self):
           super().__init__('lift_controller')
           self.client = self.create_client(LiftGPIO, '/elevator_to_robot')

       def send_lift_command(self, command):
           """
           Commands:
             0 = Hold
             1 = Lift up
             2 = Lift down
           """
           request = LiftGPIO.Request()
           request.command = command
           future = self.client.call_async(request)
           return future

Multi-Robot Setup
-----------------

For multi-robot scenarios, use namespaces to separate robot topics and frames.

Launching Multiple Robots
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Robot 1
   ROBOT_NAMESPACE=ad_r1m_0 ./bringup.sh

   # Robot 2 (on different Raspberry Pi)
   ROBOT_NAMESPACE=ad_r1m_1 ./bringup.sh

RViz for Multiple Robots
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # View robot 0
   ./start_rviz.sh 0

   # View robot 1
   ./start_rviz.sh 1

Each robot's topics will be prefixed with its namespace (e.g., ``/ad_r1m_0/cmd_vel``, ``/ad_r1m_1/cmd_vel``).
