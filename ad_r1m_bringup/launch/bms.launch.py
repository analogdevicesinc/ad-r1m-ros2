from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')

    # BMS node
    bms_node = Node(
        package='ad_r1m_bringup',
        executable='adrd_bms_node.py',
        name='bms_node',
        output='screen'
    )

    # Group node under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        bms_node
    ])

    return LaunchDescription([
        namespace_arg,
        namespaced_group
    ])
