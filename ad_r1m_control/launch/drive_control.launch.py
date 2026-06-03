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

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rosdistro = os.environ['ROS_DISTRO']
    ad_r1m_control = FindPackageShare('ad_r1m_control')

    decl_extra_control_params_file = DeclareLaunchArgument(
        'extra_control_params_file', default_value='')

    # humble-and-earlier use cmd_vel_unstamped, jazzy-and-later use cmd_vel
    humble_unstamped = '_unstamped' if rosdistro <= 'humble' else ''

    # Twist mux
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        remappings={
            ('cmd_vel_joy', 'cmd_vel_joy' + humble_unstamped),
            ('cmd_vel_out', 'diff_drive_controller/cmd_vel' + humble_unstamped),
        },
        parameters=[
            PathJoinSubstitution([ad_r1m_control, 'config', 'twist_mux.yaml']),
            {'use_stamped': rosdistro >= 'jazzy'}
        ]
    )

    # ros2_control controller_manager
    robot_control_config = PathJoinSubstitution([
        ad_r1m_control, 'config', 'controllers.yaml'
    ])
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            robot_control_config,
            LaunchConfiguration('extra_control_params_file')
        ],
        remappings=[('~/robot_description', 'robot_description')],
        output='both'
    )

    spawners = []
    for spawn, extra_args in [
        ('joint_state_broadcaster', []),
        ('diff_drive_controller', []),
        ('forward_velocity_controller', ['--inactive'])
    ]:
        spawners.append(Node(
            package='controller_manager',
            executable='spawner',
            name=[spawn, '_spawner'],
            arguments=[
                spawn,
                '--controller-manager', 'controller_manager',
                *extra_args],
            output='both',
        ))

    return LaunchDescription([
        decl_extra_control_params_file,
        twist_mux_node,
        controller_manager_node,
        *spawners
    ])
