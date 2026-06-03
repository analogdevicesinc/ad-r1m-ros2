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

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def setup_gazebo(context, *args, **kwargs):
    from launch.logging import get_logger
    logger = get_logger('robot_realsense_sim')

    package_name_gazebo = 'ad_r1m_gazebo'
    package_name_cuvslam = 'ad_r1m_perception_cuvslam'

    local_models_path = os.path.expanduser(
        LaunchConfiguration('local_models_path').perform(context))
    world_name = os.path.expanduser(
        LaunchConfiguration('world_name').perform(context))

    actions = []

    if os.path.isabs(world_name):
        world_file = world_name
    elif local_models_path:
        world_file = os.path.join(
            local_models_path.replace('/models', '/worlds'), world_name)
    else:
        world_file = os.path.join(get_package_share_directory(
            package_name_cuvslam), 'worlds', world_name)

    if local_models_path:
        if not os.path.isdir(local_models_path):
            logger.warning(
                f'local_models_path does not exist: {local_models_path}')
        existing = os.environ.get('GAZEBO_MODEL_PATH', '')
        if existing:
            os.environ['GAZEBO_MODEL_PATH'] = \
                local_models_path + os.pathsep + existing
        else:
            os.environ['GAZEBO_MODEL_PATH'] = local_models_path
        os.environ['GAZEBO_MODEL_DATABASE_URI'] = ''
        logger.info(
            f"GAZEBO_MODEL_PATH={os.environ['GAZEBO_MODEL_PATH']}")

    if not os.path.isfile(world_file):
        logger.warning(
            f'World file not found: {world_file} — '
            'Gazebo will load an empty world.')

    logger.info(f'Loading world: {world_file}')

    gazebo_params_file = os.path.join(get_package_share_directory(
        package_name_gazebo), 'config', 'gazebo_params.yaml')

    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'),
            'launch', 'gazebo.launch.py')]),
        launch_arguments={
            'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file,
            'world': world_file,
        }.items()
    ))

    return actions


def generate_launch_description():
    package_name_control = 'ad_r1m_control'
    package_name_gazebo = 'ad_r1m_gazebo'
    package_name_rviz = 'ad_r1m_description'
    package_name_cuvslam = 'ad_r1m_perception_cuvslam'

    local_models_arg = DeclareLaunchArgument(
        'local_models_path',
        default_value='',
        description='Path to local Gazebo models directory '
                    '(e.g. ~/tudor_ws/gazebo_models_worlds_collection/models). '
                    'When set, GAZEBO_MODEL_PATH is updated and world files '
                    'are loaded from a sibling worlds/ directory. '
                    'When empty, worlds from the package are used.')

    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='obstacles.world',
        description='Name of the world file to load in Gazebo')

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(
                package_name_cuvslam), 'launch', 'rsp_realsense.launch.py'
        )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    twist_mux_params = os.path.join(get_package_share_directory(
        package_name_control), 'config', 'twist_mux.yaml')
    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[twist_mux_params, {'use_sim_time': True}],
        remappings=[
            ('/cmd_vel_out', '/diff_drive_controller/cmd_vel_unstamped')]
    )

    teleop_twist_keyboard = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(
                package_name_gazebo), 'launch', 'teleopt.launch.py'
        )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'ardagv',
                                   '-x', '0.0',
                                   '-y', '0.0',
                                   '-z', '0.2',
                                   '-Y', '0.0',
                                   '-timeout', '120'],
                        output='screen')

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller'],
    )

    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
    )

    _rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(get_package_share_directory(
            package_name_rviz), 'rviz', 'main.rviz')],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    _robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(get_package_share_directory(
            package_name_control), 'config/ekf.yaml'), {'use_sim_time': True}]
    )

    return LaunchDescription([
        local_models_arg,
        world_name_arg,
        rsp,
        twist_mux,
        teleop_twist_keyboard,
        OpaqueFunction(function=setup_gazebo),
        spawn_entity,
        diff_drive_spawner,
        joint_broad_spawner,
        # robot_localization_node,
        # rviz,
    ])
