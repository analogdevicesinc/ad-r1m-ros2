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

import time
import rclpy
from rclpy.node import Node
from example_interfaces.srv import SetBool


class ElevatorServer(Node):
    """
    ElevatorServer provides a SetBool service 'elevator_to_robot'.

    When the service is called with data=True, it simulates elevator operation.
    """

    def __init__(self):
        super().__init__('elevator_server')
        self.srv = self.create_service(
            SetBool, 'elevator_to_robot', self.start_elevator_callback)
        self.get_logger().info('ElevatorServer node has been started.')

    def start_elevator_callback(self, request, response):
        if request.data:
            self.get_logger().info('Received request to start elevator')
            self.get_logger().info('Waiting for elevator to pick up the box...')
            time.sleep(6.0)  # Simulate elevator picking up the box
            response.success = True
            self.get_logger().info('Elevator done')
        else:
            response.success = False
            self.get_logger().info('Elevator request was False, not starting elevator.')
        return response


def main(args=None):
    rclpy.init(args=args)
    elevator_server = ElevatorServer()
    try:
        rclpy.spin(elevator_server)
    except KeyboardInterrupt:
        elevator_server.get_logger().info('Shutting down ElevatorServer...')
    finally:
        elevator_server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
