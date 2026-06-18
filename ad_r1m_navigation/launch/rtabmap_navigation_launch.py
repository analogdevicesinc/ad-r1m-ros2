"""
Combined RTAB-Map SLAM + Nav2 navigation launch for AD-R1M robot.

This launch file integrates:
- RTAB-Map for SLAM/localization (replaces AMCL for localization)
- Nav2 navigation stack with Vector Pursuit controller
- AD-R1M specific configurations (footprint, costmaps, behaviors)

Based on research from:
- Kunchala et al., 2026: Nav2 integration patterns with RTAB-Map
- Labbé & Michaud, 2024: RTAB-Map configuration

Usage:
    # Full SLAM + Navigation:
    ros2 launch ad_r1m_navigation rtabmap_navigation_launch.py

    # Localization + Navigation (use existing RTAB-Map database):
    ros2 launch ad_r1m_navigation rtabmap_navigation_launch.py localization:=true

    # RPi optimized:
    ros2 launch ad_r1m_navigation rtabmap_navigation_launch.py rpi_mode:=true

    # With namespace:
    ros2 launch ad_r1m_navigation rtabmap_navigation_launch.py namespace:=robot1
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    GroupAction,
    SetEnvironmentVariable,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def launch_setup(context, *args, **kwargs):
    pkg_share = FindPackageShare('ad_r1m_navigation')

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    localization = LaunchConfiguration('localization')
    rpi_mode = LaunchConfiguration('rpi_mode')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')

    namespace_str = namespace.perform(context)

    # Lifecycle nodes for Nav2 (no map_server/amcl - RTAB-Map handles localization)
    lifecycle_nodes = [
        'controller_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
    ]

    # Build remappings based on namespace
    remappings = []
    if namespace_str != '':
        remappings.append(('/scan', f'/{namespace_str}/scan'))
        remappings.append(('/map', f'/{namespace_str}/map'))

    # Parameter substitutions for Nav2
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'autostart': autostart,
    }

    if namespace_str != '':
        param_substitutions['robot_base_frame'] = f'{namespace_str}/base_link'
        param_substitutions['local_costmap.local_costmap.ros__parameters.global_frame'] = f'{namespace_str}/odom'
        param_substitutions['behavior_server.ros__parameters.global_frame'] = f'{namespace_str}/odom'

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True
    )

    nodes = []

    # ========================================
    # RTAB-Map SLAM / Localization
    # ========================================
    rtabmap_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, 'launch', 'rtabmap_rgbd_launch.py'])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time.perform(context),
            'namespace': namespace_str,
            'localization': localization.perform(context),
            'rpi_mode': rpi_mode.perform(context),
            'viz': 'false',  # Disable viz in combined launch
            'assemble_cloud': 'true',  # Enable FOV compensation
        }.items()
    )

    # ========================================
    # Nav2 Controller Server (Vector Pursuit)
    # ========================================
    nodes.append(Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        namespace=namespace,
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[configured_params],
        remappings=remappings,
    ))

    # ========================================
    # Nav2 Planner Server (NavFn)
    # ========================================
    nodes.append(Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        namespace=namespace,
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[configured_params],
        remappings=remappings,
    ))

    # ========================================
    # Nav2 Behavior Server
    # ========================================
    nodes.append(Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        namespace=namespace,
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[configured_params],
        remappings=remappings,
    ))

    # ========================================
    # Nav2 BT Navigator
    # ========================================
    nodes.append(Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        namespace=namespace,
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[configured_params],
        remappings=remappings,
    ))

    # ========================================
    # Nav2 Lifecycle Manager
    # ========================================
    nodes.append(Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'node_names': lifecycle_nodes,
        }],
    ))

    return [
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),
        rtabmap_launch,
        GroupAction(nodes),
    ]


def generate_launch_description():
    pkg_share = FindPackageShare('ad_r1m_navigation')

    return LaunchDescription([
        # ========================================
        # Launch Arguments
        # ========================================
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'),

        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace for multi-robot systems'),

        DeclareLaunchArgument(
            'localization',
            default_value='false',
            description='Use localization mode (existing RTAB-Map database) instead of SLAM'),

        DeclareLaunchArgument(
            'rpi_mode',
            default_value='false',
            description='Enable RPi optimization (reduced features, slower rate)'),

        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically startup the Nav2 stack'),

        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                pkg_share, 'config', 'rtabmap_navigation_params.yaml'
            ]),
            description='Full path to Nav2 parameters file (Vector Pursuit + RTAB-Map integration)'),

        # ========================================
        # Launch Setup
        # ========================================
        OpaqueFunction(function=launch_setup),
    ])
