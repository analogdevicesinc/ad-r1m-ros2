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
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('ad_r1m_perception_cuvslam')

    rs_config_path = LaunchConfiguration('config_path').perform(context)
    with open(rs_config_path, 'r') as rs_config_file:
        rs_config = yaml.safe_load(rs_config_file)

    foxglove_xml_config = PathJoinSubstitution([FindPackageShare(
        'ad_r1m_perception_cuvslam'), 'config', 'foxglove_bridge_launch.xml'])
    _foxglove_bridge_launch = IncludeLaunchDescription(
        XMLLaunchDescriptionSource([foxglove_xml_config])
    )

    # for multiple cameras use realsense_calibration.urdf.xacro
    urdf_file = os.path.join(
        pkg_share, 'urdf', 'single_realsense_calibration.urdf.xacro')
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    remapping_list, optical_frames = [], []
    # two physical cameras for each realsense device
    num_cameras = 2 * len(rs_config['cameras'])

    for idx in range(num_cameras):
        infra_cnt = idx % 2 + 1
        camera_cnt = rs_config['cameras'][idx // 2]['camera_name']
        optical_frames += [f'{camera_cnt}_infra{infra_cnt}_optical_frame']
        remapping_list += [(f'visual_slam/image_{idx}',
                            f'/{camera_cnt}/infra{infra_cnt}/image_rect_raw'),
                           (f'visual_slam/camera_info_{idx}',
                            f'/{camera_cnt}/infra{infra_cnt}/camera_info')]

    # This topic remap is useful for one camera (camera1) setup for imu fusion
    remapping_list += [('/visual_slam/imu', '/camera1/imu')]

    def realsense_capture(common_params, camera_params):
        stereo_capture = ComposableNode(
            name=camera_params['camera_name'],
            namespace=camera_params['camera_name'],
            package='realsense2_camera',
            plugin='realsense2_camera::RealSenseNodeFactory',
            parameters=[common_params | camera_params]
        )
        return stereo_capture

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[
            rs_config['visual_slam'] |
            {'num_cameras': num_cameras,
             'min_num_images': num_cameras,
             'camera_optical_frames': optical_frames}
        ],
        remappings=remapping_list,
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=([visual_slam_node]),
        output='screen',
    )

    realsense_image_capture = LoadComposableNodes(
        target_container='visual_slam_launch_container',
        composable_node_descriptions=([
            realsense_capture(rs_config['common_params'], camera_config)
            for camera_config in rs_config['cameras']
        ]),
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        name='realsense_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )

    return [
        # foxglove_bridge_launch,
        state_publisher,
        realsense_image_capture,
        visual_slam_launch_container
    ]


def generate_launch_description():
    pkg_share = get_package_share_directory('ad_r1m_perception_cuvslam')

    config_path_arg = DeclareLaunchArgument(
        'config_path',
        default_value=os.path.join(
            pkg_share, 'config', 'vslam_single_realsense.yaml'),
        description='Path to the YAML configuration file'
    )

    use_rosbag_arg = DeclareLaunchArgument(
        'use_rosbag',
        default_value='False',
        description='Whether to execute rosbag'
    )

    return LaunchDescription([
        config_path_arg,
        use_rosbag_arg,
        OpaqueFunction(function=launch_setup),
    ])
