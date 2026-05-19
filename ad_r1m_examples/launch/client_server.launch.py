from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace
from launch.actions import TimerAction, DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')

    server_node = Node(
        package='ad_r1m_examples',
        executable='elevator_server.py',
        name='elevator_server',
        output='screen'
    )

    client_node = Node(
        package='ad_r1m_examples',
        executable='waypoint_follower.py',
        name='waypoint_follower',
        output='screen'
    )

    # Group nodes under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        server_node,
        TimerAction(
            period=2.0,  # seconds
            actions=[client_node]
        )
    ])

    return LaunchDescription([
        namespace_arg,
        namespaced_group
    ])
