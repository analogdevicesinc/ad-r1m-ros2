#!/usr/bin/env python3

import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist, PoseWithCovarianceStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ad_r1m_examples.srv import LiftGPIO

"""
Demo script for robot navigation and lift control.

Features:
- LiftClientAsync: Asynchronous ROS2 service client for controlling a lift via GPIO.
- Waypoint: Helper class for storing navigation waypoints with orientation and lift actions.
- PoseTracker: Node that tracks robot pose, navigates through waypoints,
  and coordinates lift actions.
- Publishes navigation goals, sends velocity commands, and interacts with a lift service.
"""


class LiftClientAsync(Node):
    def __init__(self):
        super().__init__('lift_client_async')
        self.cli = self.create_client(LiftGPIO, 'elevator_to_robot')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = LiftGPIO.Request()

    def send_request(self, request):
        self.req = request
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()


class Waypoint:
    def __init__(self, x, y, angle, go_back_after=True, raise_lift=True):
        self.x = float(x)
        self.y = float(y)
        rad = math.radians(angle)
        self.z = math.sin(rad / 2)
        self.w = math.cos(rad / 2)
        self.go_back_after = bool(go_back_after)
        self.raise_lift = bool(raise_lift)

    def __getitem__(self, index):
        return [
            self.y,
            self.x,
            self.w,
            self.z,
            self.go_back_after,
            self.raise_lift][index]


class PoseTracker(Node):
    def __init__(self):
        super().__init__('pose_tracker')
        self.current_pose = Pose()
        self.navigator = BasicNavigator()
        self.goal_publisher = self.create_publisher(
            PoseStamped, '/goal_pose', 10)
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.amcl_pose_subscriber = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10
        )

        # At home:
        self.demo_route = [
            [-1.2, -0.70, 0.707, -0.707],  # -90 bottom-left
            [-1.2, 0.70, 1.0, 0.0],  # 0 bottom-right
            [1.2, 0.70, 0.707, 0.707],  # 90 top-right
            [1.2, -0.70, 0.0, 1.0],    # 180 top-left
            [0.0, 0.0, 0.707, -0.707],  # -90 center
        ]

        # Demo route:
        self.demo_route = [
            # Working together w Arduino
            Waypoint(x=0.85, y=-0.70, angle=0),
            # Screens
            Waypoint(x=0.98, y=0.60, angle=90),
            # Onsemi
            Waypoint(x=-0.90, y=0.70, angle=180),
            Waypoint(x=-0.90, y=-0.58, angle=315,
                     go_back_after=False),                 # Diagonal
            Waypoint(x=0, y=0, angle=0, go_back_after=False,
                     raise_lift=False)  # Center
        ]

        self.state = 0  # 0: idle, 1: moving, 2: lift, 3: fault
        self.call_lift_gpio(0)  # GPIO led state 0 (GREEN), lift state 0 (NOOP)

    def pose_callback(self, msg):
        self.current_pose = msg.pose.pose

    def move_backwards(self, linear_velocity, distance):
        twist = Twist()
        twist.linear.x = -linear_velocity
        start_x = self.current_pose.position.x
        start_y = self.current_pose.position.y

        while True:
            self.cmd_vel_publisher.publish(twist)
            rclpy.spin_once(self, timeout_sec=0.1)
            current_pose = self.current_pose
            distance_moved = math.sqrt(
                (current_pose.position.x - start_x) ** 2 +
                (current_pose.position.y - start_y) ** 2
            )
            if distance_moved >= distance:
                break

        twist.linear.x = 0.0
        self.cmd_vel_publisher.publish(twist)
        print('Finished moving')

    def call_lift_gpio(self, lift_state):
        lift_client = LiftClientAsync()
        request = LiftGPIO.Request()

        BLUE = 0
        GREEN = 1
        PURPLE = 2
        RED = 3

        request.led_state = {0: GREEN, 1: BLUE, 2: PURPLE, 3: RED}[self.state]
        request.lift_state = lift_state

        response = lift_client.send_request(request)
        lift_client.get_logger().info(f'Result from lift: {response.done}')
        lift_client.destroy_node()
        return response.done

    def navigate(self):
        self.navigator.waitUntilNav2Active()
        while True:
            for idx, pose in enumerate(self.demo_route, start=1):
                goal_pose = PoseStamped()
                goal_pose.header.frame_id = 'map'
                goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()
                goal_pose.pose.position.y = pose[0]
                goal_pose.pose.position.x = pose[1]
                goal_pose.pose.orientation.w = pose[2]
                goal_pose.pose.orientation.z = pose[3]

                self.goal_publisher.publish(goal_pose)
                self.navigator.goToPose(goal_pose)
                self.state = 1  # 1: moving
                self.call_lift_gpio(0)  # GPIO led 0 (GREEN), lift 0 (NOOP)

                timer = 0
                while not self.navigator.isTaskComplete():
                    timer += 1
                    feedback = self.navigator.getFeedback()
                    if feedback and timer % 10 == 0:
                        print(
                            f'Executing current waypoint: {idx}/{len(self.demo_route)}')
                    rclpy.spin_once(self, timeout_sec=0.1)

                result = self.navigator.getResult()
                if result == TaskResult.SUCCEEDED:
                    print('Goal succeeded!')
                    rclpy.spin_once(self, timeout_sec=1.0)

                    if pose.raise_lift:
                        time.sleep(1.0)
                        self.state = 2  # 2: lift
                        self.call_lift_gpio(1)  # UP
                        time.sleep(10.0)
                        self.call_lift_gpio(2)  # DOWN
                        time.sleep(2.0)

                    if pose.go_back_after:
                        self.move_backwards(0.1, 0.2)
                        print('Moving backwards for 0.1 meters')

                    if pose.raise_lift:
                        self.state = 1  # 1: moving
                        self.call_lift_gpio(0)
                        time.sleep(20)

                    time.sleep(2.0)

                elif result == TaskResult.CANCELED:
                    print('Goal was canceled!')
                    self.state = 3  # 3: fault
                    self.call_lift_gpio(0)
                elif result == TaskResult.FAILED:
                    print('Goal failed!')
                    self.state = 3  # 3: fault
                    self.call_lift_gpio(0)

            self.state = 0  # 0: idle
            self.call_lift_gpio(0)
            time.sleep(3.0)


def main():
    rclpy.init()
    pose_tracker = PoseTracker()
    pose_tracker.navigate()
    rclpy.spin(pose_tracker)
    pose_tracker.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
