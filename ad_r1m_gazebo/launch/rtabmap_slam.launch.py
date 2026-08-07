#!/usr/bin/env python3
"""
RTAB-Map SLAM Launch File for AD-R1M Gazebo Simulation

Alternative to SLAM Toolbox for mapping in simulation.
Uses /scan (LaserScan from simulated lidar) for mapping.

Based on rtab-scan.launch.py but configured for simulation use.

Usage:
    # Start simulation first:
    ros2 launch ad_r1m_gazebo launch_sim.launch.py

    # Then start RTAB-Map SLAM:
    ros2 launch ad_r1m_gazebo rtabmap_slam.launch.py

    # For localization mode (use existing map):
    ros2 launch ad_r1m_gazebo rtabmap_slam.launch.py localization:=true
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    localization = LaunchConfiguration('localization').perform(context)
    localization = localization.lower() == 'true'
    namespace = LaunchConfiguration('namespace').perform(context)

    # Build frame names based on namespace
    if namespace:
        base_frame = f'{namespace}/base_link'
        odom_frame = f'{namespace}/odom'
    else:
        base_frame = 'base_link'
        odom_frame = 'odom'

    parameters = {
        'frame_id': base_frame,
        'odom_frame_id': odom_frame,
        'use_sim_time': use_sim_time,
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_scan': True,
        'approx_sync': True,
        'use_action_for_goal': True,

        # ICP registration (Strategy=1 for scan-only)
        'Reg/Strategy': '1',
        'Reg/Force3DoF': 'true',

        # Loop closure refinement
        'RGBD/NeighborLinkRefining': 'True',

        # Laser scan range (matches simulation lidar config)
        'Grid/RangeMin': '0.4',
        'Grid/RangeMax': '5.0',

        # Disable IMU constraints (2D mode)
        'Optimizer/GravitySigma': '0',

        # Grid parameters for occupancy grid
        'Grid/CellSize': '0.05',
        'Grid/FromDepth': 'false',

        # Map update frequency
        'Rtabmap/DetectionRate': '1.0',
    }

    arguments = []
    if localization:
        parameters['Mem/IncrementalMemory'] = 'False'
        parameters['Mem/InitWMWithAllNodes'] = 'True'
    else:
        arguments.append('-d')  # Delete database on start

    # Remappings - adjust based on namespace
    if namespace:
        remappings = [
            ('scan', f'/{namespace}/scan'),
            ('odom', f'/{namespace}/odometry/filtered'),
        ]
    else:
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
            namespace=namespace if namespace else None,
            output='screen',
            parameters=[parameters],
            remappings=remappings,
            arguments=arguments,
        ),

        # RTAB-Map Viz (optional, for debugging)
        # Uncomment to visualize RTAB-Map internal state
        # Node(
        #     package='rtabmap_viz',
        #     executable='rtabmap_viz',
        #     name='rtabmap_viz',
        #     namespace=namespace if namespace else None,
        #     output='screen',
        #     parameters=[{'use_sim_time': use_sim_time}],
        # ),
    ]

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock'),
        DeclareLaunchArgument(
            'localization',
            default_value='false',
            description='Set to true for localization mode (use existing map)'),
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace for multi-robot systems'),
        OpaqueFunction(function=launch_setup),
    ])
