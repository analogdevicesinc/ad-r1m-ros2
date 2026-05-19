from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )

    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('ad_r1m_bringup'), 'config', 'crsf.yaml']),
        description='Path to CRSF parameters file'
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')

    # Create CRSF node
    crsf_node = Node(
        package='ad_r1m_bringup',
        executable='crsf_node.py',
        name='crsf_node',
        parameters=[params_file],
        output='screen'
    )

    # Group node under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        crsf_node
    ])

    return LaunchDescription([
        namespace_arg,
        params_file_arg,
        namespaced_group
    ])
