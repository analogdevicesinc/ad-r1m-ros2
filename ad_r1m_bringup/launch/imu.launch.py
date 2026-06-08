from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    # Launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )
    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        description='The TF frame ID for the IMU sensor (e.g., source_x/imu).',
        default_value=PythonExpression([
            "'", LaunchConfiguration('namespace'), "/imu'.lstrip('/')",
            " if '", LaunchConfiguration('namespace'), "' else 'imu'"
        ])
    )

    # Get launch configurations
    namespace = LaunchConfiguration('namespace')
    frame_id = LaunchConfiguration('frame_id')

    # Create IMU node
    imu_node = Node(
        package='adi_imu',
        executable='adi_imu_node',
        name='imu_node',
        parameters=[
            {'iio_context_string': 'local:'},
            {'measured_data_topic_selection': 2},
            {'imu_device_name': 'adis16470'},
            {'diag_data_enable': False},
            {'ident_data_enable': False},
            {'frame_id': frame_id},
            {'covariance': {
                'enabled': True,
            }}
        ],
        output='screen'
    )

    # Group node under namespace
    namespaced_group = GroupAction([
        PushRosNamespace(namespace),
        imu_node
    ])

    return LaunchDescription([
        namespace_arg,
        frame_id_arg,
        namespaced_group
    ])
