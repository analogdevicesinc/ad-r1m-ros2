# Copyright 2019 Open Source Robotics Foundation, Inc.
# Copyright (c) 2025-2026 Analog Devices, Inc.
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

# Author: Gary Liu
# Author: Laurentiu Popa

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node, PushRosNamespace

def generate_launch_description():
    # Declare launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )
    param_file_arg = DeclareLaunchArgument(
        'param_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('ad_r1m_perception_aditof'),
            'config', 'depth_to_laser_params.yaml']),
        description='Path to depth-to-laser parameter file'
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')
    param_file = LaunchConfiguration('param_file')

    # Create frame_id that includes namespace if provided
    output_frame = PythonExpression([
        "'", namespace, "/cam1_scan' if '", namespace, "' else 'cam1_scan'"
    ])

    # Create depthimage_to_laserscan node
    node_depthimage_to_laserscan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        remappings=[('depth', '/cam1/depth_image'),
                    ('depth_camera_info', '/cam1/camera_info'),
                    ('scan', 'scan')],
        output='screen',
        parameters=[
            param_file,
            {'output_frame': output_frame}
        ]
    )

    # Group node under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        node_depthimage_to_laserscan
    ])

    return LaunchDescription([
        namespace_arg,
        param_file_arg,
        namespaced_group
    ])
