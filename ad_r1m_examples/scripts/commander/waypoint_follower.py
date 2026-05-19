#! /usr/bin/env python3
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from example_interfaces.srv import SetBool
from rclpy.node import Node
import rclpy

"""
Basic navigation demo to go to poses and interact with a ROS2 service after each goal.
"""


class ElevatorClientAsync(Node):
    """
    Async client for the 'elevator_to_robot' SetBool service.

    - Waits for service on init.
    - send_request(bool) sends a request and returns the response.
    """

    def __init__(self):
        super().__init__('elevator_client_async')
        print("Waiting for 'elevator_to_robot' service...")
        self.cli = self.create_client(SetBool, 'elevator_to_robot')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
            print('Service not available, waiting again...')
        print("'elevator_to_robot' service is now available.")
        self.req = SetBool.Request()

    def send_request(self, start_elevator: bool):
        print(
            f"Sending request to 'elevator_to_robot' service with data: {start_elevator}")
        self.req.data = start_elevator
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        print("Received response from 'elevator_to_robot' service.")
        return self.future.result()


def run_navigator(navigator: BasicNavigator, route: list,
                  elevator_client: ElevatorClientAsync):
    """
    Navigate through a list of waypoints and interact with a ROS2 service after each goal.

    Args:
    ----
        navigator (BasicNavigator): The Nav2 navigation client.
        route (list): List of waypoints [x, y, w, z].
        elevator_client (ElevatorClientAsync): ROS2 service client for 'elevator_to_robot'.

    """
    for i, pose in enumerate(route, 1):
        print(f'Navigating to waypoint {i}/{len(route)}: {pose}')
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = navigator.get_clock().now().to_msg()
        goal_pose.pose.position.x, goal_pose.pose.position.y = pose[0], pose[1]
        goal_pose.pose.orientation.w, goal_pose.pose.orientation.z = pose[2], pose[3]
        navigator.goToPose(goal_pose)

        timer = 0
        while not navigator.isTaskComplete():
            timer += 1
            if navigator.getFeedback() and timer % 10 == 0:
                print(f'Executing current waypoint: {i}/{len(route)}')

        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            print('Goal succeeded!')
            # Call the ROS2 service after reaching the goal
            print('Calling elevator service after reaching goal...')
            resp = elevator_client.send_request(True)
            elevator_client.get_logger().info(
                f'Result of receive_bool: for {resp.success}')
            print(
                f'Elevator service responded with: success={resp.success}, '
                f"message='{resp.message}'")
        elif result == TaskResult.CANCELED:
            print('Goal was canceled!')
        elif result == TaskResult.FAILED:
            print('Goal failed!')


def main():
    print('Initializing ROS2 node...')
    rclpy.init()
    navigator = BasicNavigator()

    # Define route as a list of waypoints: [x, y, w, z]
    route = [
        [0.70, 1.10, 0.707, 0.707],  # 90° top-right
        [-0.70, 1.10, 0.707, -0.707],   # -90° top-left
        [-0.70, -1.10, 0.707, -0.707],  # -90° bottom-left
        [0.70, -1.10, 0.707, 0.707],  # 90° bottom-right
        [0.7, 1.10, 0.707, 0.707]  # 90° top-right again, complete the loop
    ]
    print(f'Route defined with {len(route)} waypoints.')

    # Set initial pose: center of the map, -90°
    print('Setting initial pose...')
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 0.707
    initial_pose.pose.orientation.z = -0.707
    navigator.setInitialPose(initial_pose)

    # Wait for navigation to fully activate, since autostarting nav2
    print('Waiting for Nav2 to become active...')
    navigator.waitUntilNav2Active()
    print('Nav2 is active.')

    elevator_client = ElevatorClientAsync()
    run_navigator(navigator, route, elevator_client)

    print('Shutting down elevator client node...')
    elevator_client.destroy_node()
    print('Shutting down ROS2...')
    rclpy.shutdown()
    print('Done.')


if __name__ == '__main__':
    main()
