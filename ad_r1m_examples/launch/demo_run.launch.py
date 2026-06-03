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

from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace
from launch.actions import TimerAction, DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    start_lift_arg = DeclareLaunchArgument(
        'start_lift',
        default_value='false',
        description='Whether to start the lift and gpios node'
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')

    demo_run_node = Node(
        package='ad_r1m_examples',
        executable='demo_run.py',
        name='demo_run_node',
        output='screen'
    )

    lift_node = Node(
        package='ad_r1m_examples',
        executable='lift_node.py',
        name='lift_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('start_lift'))
    )

    # Group nodes under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        demo_run_node,
        TimerAction(
            period=5.0,
            actions=[lift_node]
        )
    ])

    return LaunchDescription([
        namespace_arg,
        start_lift_arg,
        namespaced_group
    ])
