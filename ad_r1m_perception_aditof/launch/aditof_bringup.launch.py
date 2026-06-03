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
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, Shutdown
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_3dtof_adtf31xx_dir = FindPackageShare('adi_3dtof_adtf31xx')
    pkg_ad_r1m_perception_aditof_dir = FindPackageShare(
        'ad_r1m_perception_aditof')

    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    camera_namespace_arg = DeclareLaunchArgument(
        'camera_namespace',
        default_value='cam1',
        description='Camera namespace (default: cam1)'
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')
    camera_namespace = LaunchConfiguration('camera_namespace')

    # ToF camera node
    adi_3dtof_adtf31xx_node_desc = Node(
        package='adi_3dtof_adtf31xx',
        namespace=camera_namespace,
        executable='adi_3dtof_adtf31xx_node',
        name='adi_3dtof_adtf31xx_node',
        output='screen',
        parameters=[{
            'param_camera_link': 'cam1_adtf31xx_optical',
            'param_input_sensor_mode': 0,
            'param_config_file_name_of_tof_sdk': (  # noqa: E501
                pkg_3dtof_adtf31xx_dir + '/config/config_adsd3500_adsd3100.json'
            ),
            'param_camera_mode': 3,
            'param_enable_depth_ab_compression': False,
            'param_enable_depth_publish': True,
            'param_enable_ab_publish': True,
            'param_enable_conf_publish': False,
            'param_enable_point_cloud_publish': True,
            'param_ab_threshold': 10,
            'param_confidence_threshold': 10,
            'param_encoding_type': '16UC1',
            'param_input_sensor_ip': ''
        }],
        on_exit=Shutdown()
    )

    # Depth image to laser scan converter
    depth_image_to_laserscan_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_ad_r1m_perception_aditof_dir, 'launch',
                                  'depthimage_to_laserscan.launch.py'])
        ),
    )

    # Group nodes under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        adi_3dtof_adtf31xx_node_desc,
        depth_image_to_laserscan_node
    ])

    return LaunchDescription([
        namespace_arg,
        camera_namespace_arg,
        namespaced_group
    ])
