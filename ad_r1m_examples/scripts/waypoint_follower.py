#!/usr/bin/env python3
# Copyright (c) 2026 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from dataclasses import dataclass
import rclpy
from rclpy.node import Node
import math

"""

Robot arena positions:

 (-1.4, -1.05)      (0, -1.05)       (+1.4, -1.05)
       +----------------------------------+
       |                :                 |
       |   [1]          :       [3]       |
       |                :                 |
       |                : (0,0)           |
       |- - - - - - - - + - - - - - - - - |
       |                :                 |
       |                :                /
       |   [0]        [2]         [4]   /
       |                :              /
       +------------------------------'   +
 (-1.4, +1.05)      (0, +1.05)            (+1.4, +1.05)


Headings: 0 = East, 90 = North, 180 = West, 270 = South

[0], [1], [2], [3], [4]: Example waypoints tracing an "M" shape

You should set your targets ~40-50cm from the edge. The robot will refuse to
come too close to the edge.

"""


@dataclass
class Waypoint:
    """Helper class for specifying 2D poses with just x, y, heading."""

    x: float
    y: float
    heading: float  # Degrees

    def as_pose(self):
        """Convert Waypoint to ROS 2 PoseStamped object, to be sent to nav2."""
        # Compute quaternion for heading
        rad = math.radians(self.heading)
        quat_z = math.sin(rad / 2)
        quat_w = math.cos(rad / 2)

        # Build PoseStamped object with the waypoint's position and orientation
        pose = PoseStamped()
        pose.header.frame_id = 'map'  # Generated pose is relative to map frame
        pose.pose.position.x = self.x
        pose.pose.position.y = self.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = quat_z
        pose.pose.orientation.w = quat_w

        return pose

    def __repr__(self):
        return f'Waypoint(x={self.x:.2f}, y={self.y:.2f}, heading={self.heading:.0f})'


def main():
    # ROS 2 initialization
    rclpy.init()
    nav = BasicNavigator()
    node = Node('waypoint_navigator')
    goal_pose_pub = node.create_publisher(PoseStamped, 'goal_pose', 1)

    # Wait for nav2 to be up and running
    nav.waitUntilNav2Active()

    # ____________________ CHANGE THIS ____________________
    # fmt: off
    # autopep8: off
    waypoints = [
        Waypoint(x = -0.9 , y = -0.5 , heading = 90.0 ),  # noqa
        Waypoint(x = -0.9 , y = +0.5 , heading = 0.0 ),  # noqa
        Waypoint(x =  0.0 , y = -0.5 , heading = 300.0 ),  # noqa
        Waypoint(x = +0.9 , y = +0.5 , heading = 270.0 ),  # noqa
        Waypoint(x = +0.9 , y = -0.2 , heading = 180.0  ),  # noqa
    ]
    # autopep8: on
    # fmt: on
    # ^^^^^^^^^^^^^^^^^^^^ CHANGE THIS ^^^^^^^^^^^^^^^^^^^^

    for index, waypoint in enumerate(waypoints):
        print(f'Going to waypoint {index}: {waypoint}')

        # Send command
        pose = waypoint.as_pose()
        pose.header.stamp = node.get_clock().now().to_msg()
        goal_pose_pub.publish(pose)
        nav.goToPose(pose)

        # Loop until command is executed
        while not nav.isTaskComplete():
            nav.getFeedback()
            rclpy.spin_once(node, timeout_sec=0.1)

        # Check result
        result = nav.getResult()
        if result == TaskResult.SUCCEEDED:
            print('SUCCESS!')
        elif result == TaskResult.CANCELED:
            print('Canceled')
        elif result == TaskResult.FAILED:
            (error_code, error_msg) = nav.getTaskError()
            print(f"Couldn't execute waypoint {index}: {waypoint}")
            print(f'{result=}')
            print(f'{error_code=} {error_msg}')

        # Wait 5 seconds on each waypoint
        # time.sleep(5)


if __name__ == '__main__':
    main()
