from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command


def generate_launch_description():
    # Package share directories
    ad_r1m_bringup = FindPackageShare('ad_r1m_bringup')
    ad_r1m_control = FindPackageShare('ad_r1m_control')

    # Launch arguments
    decl_namespace = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )
    decl_can_iface = DeclareLaunchArgument('can_iface', default_value='can0')
    decl_robot_xacro = DeclareLaunchArgument('robot_xacro', default_value=
        PathJoinSubstitution([FindPackageShare('ad_r1m_bringup'),
                             'urdf', 'ad_r1m_canopen.urdf.xacro']))

    namespace = LaunchConfiguration('namespace')
    can_iface = LaunchConfiguration('can_iface')
    robot_xacro = LaunchConfiguration('robot_xacro')

    # Start ros2_control stack (includes RSP)
    drive_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('ad_r1m_control'),
                                  'launch', 'drive_control.launch.py'
                                  ])
        ),
        launch_arguments={
            'namespace': namespace,
            'can_iface': can_iface,
            'robot_xacro': robot_xacro,
        }.items()
    )

    bringup_imu = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ad_r1m_bringup, 'launch', 'imu.launch.py'])
        ),
        launch_arguments={
            'namespace': namespace
        }.items()
    )

    bringup_sensor_fusion = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                ad_r1m_control, 'launch', 'sensor_fusion.launch.py'
            ])
        ),
        launch_arguments={
            'namespace': namespace
        }.items()
    )

    # bringup_bms = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         PathJoinSubstitution([ad_r1m_bringup, 'launch', 'bms.launch.py'])
    #     ),
    #     launch_arguments={
    #         'namespace': namespace
    #     }.items()
    # )

    return LaunchDescription([
        decl_namespace,
        decl_can_iface,
        decl_robot_xacro,

        drive_control,
        bringup_imu,
        bringup_sensor_fusion,
    ])
