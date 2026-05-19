from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, GroupAction


def generate_launch_description():
    # Get launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')

    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use sim time if true'
    )

    # Create teleop_twist_keyboard node
    teleop_keyboard_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        prefix='xterm -e',
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', 'cmd_vel_keyboard')]
    )

    # Group node under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        teleop_keyboard_node
    ])

    return LaunchDescription([
        use_sim_time_arg,
        namespace_arg,
        namespaced_group
    ])
