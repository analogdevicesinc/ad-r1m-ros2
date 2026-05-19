#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Barebones app that sends a sequence of cmd_vel messages to an AD-R1M robot with set durations.
Showcases ROS 2 boilerplate, manipulating a message and using a publisher to send it to the robot, timers and rclpy executor spinning.

Copyright (c) 2026 Analog Devices, Inc.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math


def main():
    # ROS 2 initialization boilerplate
    rclpy.init()
    node = Node('velocity_control_example')

    # Objects for continuously transmitting velocity command:

    # Publisher object sends messages to a topic
    cmd_vel_pub = node.create_publisher(Twist, 'cmd_vel', 1)

    # Message object will be populated with data and passed to publisher
    cmd_vel_msg = Twist()

    # Sentinel value
    DEADLINE_OVER = rclpy.time.Time(seconds=0)

    # Deadline object tracks time at which a command should stop being
    # re-transmitted
    deadline = DEADLINE_OVER

    def set_velocity_for(linear: float, angular: float, duration: float):
        """
        Set robot velocity for a set duration, then stop.

        Multiple overlapping calls keep the last values.

        :param float linear: Linear velocity in m/s. Positive = forward.
        :param float angular: Angular velocity in rad/s. Positive = turn left.
        :param float duration: In how much time from now to stop, in seconds.
        """

        # Need to nonlocal variables we're modifying
        nonlocal deadline
        nonlocal cmd_vel_msg

        node.get_logger().debug(
            f'Setting velocity to {linear} m/s forward, '
            f'{angular} rad/s left for {duration} s')
        cmd_vel_msg.linear.x = float(linear)
        cmd_vel_msg.angular.z = float(angular)
        deadline = node.get_clock().now() + rclpy.duration.Duration(seconds=duration)

    def timer_tick():
        """
        Function called on a timer; handles retransmitting velocity and handling deadlines (stop).
        """

        # Need to nonlocal variables we're modifying
        nonlocal deadline
        nonlocal cmd_vel_msg

        # Don't repeatedly transmit velocity once stopped
        if deadline.nanoseconds == 0:
            return

        # Handle stop condition
        if deadline < node.get_clock().now():
            node.get_logger().info('Stopped')
            cmd_vel_msg.linear.x = 0.0
            cmd_vel_msg.angular.z = 0.0
            deadline = DEADLINE_OVER

        cmd_vel_pub.publish(cmd_vel_msg)

    # TIMER_PERIOD needs to be quicker than the twist_mux timeout for robot
    # not to stutter (0.1)
    TIMER_PERIOD = 0.05
    node.create_timer(TIMER_PERIOD, timer_tick)

    ####################################################
    # EXAMPLE SEQUENCE OF HARD-CODED VELOCITY COMMANDS #
    ####################################################

    # autopep8: off
    example_commands = [
        # linear,   angular,    duration,       message
        (0.5,       0,          1,              "Go forward 0.5m/s * 1s = 0.5m"),
        (0, 0, 1, ""),
        (0,         1,          math.pi / 2,    "Turn left 1rad/s * pi/2 s = 90 degrees"),
        (0, 0, 1, ""),
        (1,         0,          0.5,            "Go forward 1m/s * 0.5s = 0.5m"),
        (0, 0, 1, ""),
        (0,         -math.pi/4, 6,             "Turn right pi/4 rad/s * 6 s = 270 degrees"),
        (0, 0, 1, ""),
    ] * 2 # Repeat list twice, to trace a square
    # autopep8: on

    for linear, angular, duration, message in example_commands:
        node.get_logger().info(message)
        set_velocity_for(linear, angular, duration)

        # Let rclpy do its thing until we hit the deadline
        while deadline.nanoseconds != 0:
            rclpy.spin_once(node)

    # ROS 2 cleanup
    node.get_logger().info('DONE!')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
