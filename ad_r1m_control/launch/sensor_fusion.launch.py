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
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    decl_ekf_config_file = DeclareLaunchArgument(
        'ekf_config_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('ad_r1m_control'), 'config', 'ekf.yaml']),
        description='Path to EKF configuration file'
    )

    decl_namespace = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    ekf_config_file = LaunchConfiguration('ekf_config_file')
    namespace = LaunchConfiguration('namespace')

    ekf_filter_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            ekf_config_file,
            {
                'use_sim_time': False,
                'tf_prefix': namespace
            }
        ]
    )

    return LaunchDescription([
        decl_ekf_config_file,
        decl_namespace,

        PushRosNamespace(namespace),
        ekf_filter_node,
    ])
