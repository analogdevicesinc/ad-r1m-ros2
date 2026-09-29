#!/usr/bin/env python3
"""
RTAB-Map Scan SLAM Launch File for AD-R1M Robot

Minimal scan-only configuration based on turtlebot3_scan.launch.py.
Uses /scan (LaserScan from depthimage_to_laserscan) for mapping.
Uses /cam1/point_cloud for obstacles_detection (Nav2 obstacle avoidance).

Tested and working on AD-R1M robot with ToF camera.

Research-backed:
- Labbé & Michaud, 2024: ICP with external odometry achieves 0.07m ATE
- Paper shows RTAB-Map auto-configures Grid/Sensor=0 for scan input
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    localization = LaunchConfiguration('localization').perform(context)
    localization = localization == 'True' or localization == 'true'

    # Minimal parameters - let RTAB-Map auto-configure Grid/Sensor
    parameters = {
        'frame_id': 'base_link',
        'use_sim_time': use_sim_time,
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_scan': True,
        'approx_sync': True,
        'use_action_for_goal': True,

        # ICP registration (Strategy=1)
        'Reg/Strategy': '1',
        'Reg/Force3DoF': 'true',

        # Loop closure refinement
        'RGBD/NeighborLinkRefining': 'True',

        # Laser scan range
        'Grid/RangeMin': '0.2',

        # Disable IMU constraints (2D mode)
        'Optimizer/GravitySigma': '0',
    }

    arguments = []
    if localization:
        parameters['Mem/IncrementalMemory'] = 'False'
        parameters['Mem/InitWMWithAllNodes'] = 'True'
    else:
        arguments.append('-d')  # Delete database on start

    remappings = [
        ('scan', '/scan'),
        ('odom', '/odometry/filtered'),
    ]

    nodes = [
        # RTAB-Map SLAM
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[parameters],
            remappings=remappings,
            arguments=arguments,
        ),

        # obstacles_detection for Nav2 using ToF point cloud
        Node(
            package='rtabmap_util',
            executable='obstacles_detection',
            name='obstacles_detection',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_link',
                'wait_for_transform': 0.2,
                'Grid/MaxGroundHeight': '0.05',
                'Grid/MaxObstacleHeight': '1.5',
                'Grid/NormalsSegmentation': 'false',
                'Grid/MinClusterSize': '10',
            }],
            remappings=[
                ('cloud', '/cam1/point_cloud'),
                ('obstacles', 'camera/obstacles'),
                ('ground', 'camera/ground'),
            ],
        ),
    ]

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('localization', default_value='false'),
        OpaqueFunction(function=launch_setup),
    ])
