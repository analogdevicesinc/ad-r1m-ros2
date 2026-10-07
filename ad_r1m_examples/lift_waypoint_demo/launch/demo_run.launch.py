from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace
from launch.actions import TimerAction, DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    start_lift_arg = DeclareLaunchArgument(
        'start_lift',
        default_value='false',
        description='Whether to start the lift and gpios node'
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')

    demo_run_node = Node(
        package='ad_r1m_examples',
        executable='demo_run.py',
        name='demo_run_node',
        output='screen'
    )

    lift_node = Node(
        package='ad_r1m_examples',
        executable='lift_node.py',
        name='lift_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('start_lift'))
    )

    # Group nodes under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        demo_run_node,
        TimerAction(
            period=5.0,
            actions=[lift_node]
        )
    ])

    return LaunchDescription([
        namespace_arg,
        start_lift_arg,
        namespaced_group
    ])
