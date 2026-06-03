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

import sys
import threading
import os
import yaml
import termios
import tty
import argparse
import time

import geometry_msgs.msg
import rclpy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from ament_index_python.packages import get_package_share_directory


msg = """
Differential Drive Robot - Keyboard Teleop
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

i/,   : forward/backward
j/l   : turn left/right
u/o/m/. : combined movements

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

p/r : activate/reset killswitch

CTRL-C to quit
"""

moveBindings = {
    'i': (1, 0), 'o': (1, -1), 'j': (0, 1), 'l': (0, -1),
    'u': (1, 1), ',': (-1, 0), '.': (-1, 1), 'm': (-1, -1),
}

speedBindings = {
    'q': (1.1, 1.1), 'z': (.9, .9), 'w': (1.1, 1),
    'x': (.9, 1), 'e': (1, 1.1), 'c': (1, .9),
}


def getKey(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed, turn):
    return f'currently:\tspeed {speed:.2f}\tturn {turn:.2f}'


def load_config(params_file=None):
    """
    Load parameters from YAML file, return defaults if not found.

    :param params_file: Path to custom YAML file. If None, uses default crsf.yaml.
    """
    defaults = {
        'max_vel': 0.5,
        'max_rot': 1.0,
        'stamped': False,
        'frame_id': '',
        'kill_sequence': [
            'drive_left/halt',
            'drive_right/halt'
        ],
        'init_sequence': [
            'drive_left/init',
            'drive_right/init',
            'drive_left/velocity_mode',
            'drive_right/velocity_mode'
        ]
    }

    try:
        if params_file:
            config_path = params_file
        else:
            pkg_dir = get_package_share_directory('ad_r1m_real')
            config_path = os.path.join(pkg_dir, 'config', 'crsf.yaml')

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            kb_params = config.get('teleop_keyboard', {}).get(
                'ros__parameters', {})
            crsf_params = config.get('crsf_node', {}).get(
                'ros__parameters', {})

            return {
                'max_vel': kb_params.get('max_vel', defaults['max_vel']),
                'max_rot': kb_params.get('max_rot', defaults['max_rot']),
                'stamped': kb_params.get('stamped', defaults['stamped']),
                'frame_id': kb_params.get('frame_id', defaults['frame_id']),
                'kill_sequence': crsf_params.get('kill_sequence', defaults['kill_sequence']),
                'init_sequence': crsf_params.get('init_sequence', defaults['init_sequence'])
            }
    except Exception as e:
        print(f'Warning: Could not load config: {e}')
        return defaults


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Keyboard teleop for differential drive robot')
    parser.add_argument(
        '--params_file',
        type=str,
        default=None,
        help='Path to custom YAML parameters file (default: uses package crsf.yaml)')

    # Separate ROS args from script args
    ros_args = []
    script_args = []
    i = 0
    argv = sys.argv[1:]

    while i < len(argv):
        if argv[i] == '--ros-args':
            # Everything after --ros-args goes to ROS
            ros_args.extend(argv[i:])
            break
        else:
            script_args.append(argv[i])
            i += 1

    # Parse only script arguments
    args = parser.parse_args(script_args)

    settings = termios.tcgetattr(sys.stdin)
    rclpy.init(args=ros_args)
    node = rclpy.create_node('teleop_keyboard')

    # Load config
    config = load_config(params_file=args.params_file)
    speed = 0.5 * config['max_vel']
    turn = config['max_rot']

    if args.params_file:
        node.get_logger().info(f'Loaded config from: {args.params_file}')

    node.get_logger().info(
        f"max_vel: {config['max_vel']}, max_rot: {config['max_rot']}")
    node.get_logger().info(f'Initial speed: {speed}, turn: {turn}')

    # Create service clients for motor control
    stop_services = [node.create_client(Trigger, s)
                     for s in config['kill_sequence']]
    start_services = [node.create_client(Trigger, s)
                      for s in config['init_sequence']]

    # Wait for motor services
    node.get_logger().info('Waiting for motor services...')
    for cli in stop_services + start_services:
        while not cli.wait_for_service(timeout_sec=5.0):
            node.get_logger().info(f'Waiting for {cli.srv_name}')
    node.get_logger().info('All motor services available!')

    # Setup publishers
    if config['stamped']:
        pub = node.create_publisher(
            geometry_msgs.msg.TwistStamped, 'cmd_vel_keyboard', 10)
        twist_msg = geometry_msgs.msg.TwistStamped()
        twist_msg.header.frame_id = config['frame_id']
        twist = twist_msg.twist
    else:
        pub = node.create_publisher(
            geometry_msgs.msg.Twist, 'cmd_vel_keyboard', 10)
        twist_msg = geometry_msgs.msg.Twist()
        twist = twist_msg

    killswitch_pub = node.create_publisher(Bool, 'killswitch', 1)
    killswitch_state = [False]

    def killswitch_callback(msg):
        killswitch_state[0] = msg.data
        node.get_logger().info(f'Killswitch state: {msg.data}')

    node.create_subscription(Bool, 'killswitch', killswitch_callback, 10)
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    x = th = status = 0.0
    state = 'init'

    def call_services(services):
        """Call motor services sequentially and wait for completion."""
        futures = []
        for i, cli in enumerate(services):
            node.get_logger().info(f'Calling service {cli.srv_name}')
            future = cli.call_async(Trigger.Request())
            # Wait for this service to complete before calling the next
            rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
            futures.append(future)

            # Add longer delay after init services to let motors fully
            # initialize
            if 'init' in cli.srv_name:
                node.get_logger().info(
                    f'Waiting for motor {cli.srv_name} to fully initialize...')
                time.sleep(2.0)  # Longer delay after init
            elif i < len(services) - 1:  # Regular delay between other services
                time.sleep(0.2)

        return futures

    def update_twist():
        """Update and publish twist message."""
        if config['stamped']:
            twist_msg.header.stamp = node.get_clock().now().to_msg()
        twist.linear.x = x * speed
        twist.angular.z = th * turn

        pub.publish(twist_msg)

    try:
        print(msg)
        print(vels(speed, turn))

        # Safety: Wait for intentional killswitch activation
        while state == 'init':
            if killswitch_state[0]:
                state = 'kill'
                node.get_logger().info('Killswitch active, press "r" to enable')
                break
            node.get_logger().info('Safety: Press "p" to activate killswitch first')
            key = getKey(settings)
            if key == 'p':
                killswitch_pub.publish(Bool(data=True))
                state = 'kill'
            elif key == '\x03':
                raise KeyboardInterrupt()

        # Main control loop
        while True:
            key = getKey(settings)

            if state == 'kill':
                if key == 'r':
                    killswitch_pub.publish(Bool(data=False))
                    killswitch_state[0] = False
                    node.get_logger().info('INITIALIZING')
                    futures = call_services(start_services)

                    # Check if all motor services succeeded
                    failed_services = []
                    for i, future in enumerate(futures):
                        service_name = start_services[i].srv_name
                        if not future.done():
                            node.get_logger().error(
                                f'Service {service_name} did not complete')
                            failed_services.append(service_name)
                        elif not future.result():
                            node.get_logger().error(
                                f'Service {service_name} returned no result')
                            failed_services.append(service_name)
                        elif not future.result().success:
                            result = future.result()
                            node.get_logger().error(
                                f'Service {service_name} failed: {result.message}')
                            failed_services.append(service_name)
                        else:
                            node.get_logger().info(
                                f'Service {service_name} succeeded')

                    if not failed_services:
                        node.get_logger().info(
                            'Motor initialization successful, waiting before enabling control...')
                        # Allow motors time to enter velocity mode
                        time.sleep(2.0)
                        state = 'run'
                        node.get_logger().info('Control enabled!')
                        print(msg)
                        print(vels(speed, turn))
                    else:
                        node.get_logger().error(
                            f'Motor initialization failed for services: {failed_services}')
                        state = 'kill'
                elif key == '\x03':
                    break
                x = th = 0.0

            elif state == 'run':
                if key in moveBindings:
                    x, th = moveBindings[key]
                elif key in speedBindings:
                    speed = min(
                        speed * speedBindings[key][0], config['max_vel'])
                    turn = min(turn * speedBindings[key][1], config['max_rot'])
                    print(vels(speed, turn))
                    if status == 14:
                        print(msg)
                    status = (status + 1) % 15
                    continue  # Skip publishing when adjusting speed
                elif key == 'p':
                    killswitch_pub.publish(Bool(data=True))
                    killswitch_state[0] = True
                    state = 'kill'
                    x = th = 0.0
                    node.get_logger().info('KILLSWITCH')
                    call_services(stop_services)
                elif key == '\x03':
                    break
                else:
                    x = th = 0.0

            # Force zero velocity when not running
            if state != 'run' or killswitch_state[0]:
                x = th = 0.0

            update_twist()

    except Exception as e:
        print(e)
    finally:
        twist.linear.x = twist.angular.z = 0.0
        update_twist()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == '__main__':
    main()
