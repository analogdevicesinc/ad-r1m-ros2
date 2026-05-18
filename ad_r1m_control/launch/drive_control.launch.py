import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, Command
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rosdistro = os.environ['ROS_DISTRO']
    ad_r1m_control = FindPackageShare('ad_r1m_control')

    decl_namespace = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
    )
    decl_can_iface = DeclareLaunchArgument('can_iface', default_value='can0')
    decl_robot_xacro = DeclareLaunchArgument('robot_xacro', default_value=
        PathJoinSubstitution([FindPackageShare('ad_r1m_bringup'),
                             'urdf', 'ad_r1m_canopen.urdf.xacro']))
    decl_extra_control_params_file = DeclareLaunchArgument('extra_control_params_file', default_value='')

    namespace = LaunchConfiguration('namespace')
    can_iface = LaunchConfiguration('can_iface')
    robot_xacro = LaunchConfiguration('robot_xacro')

    robot_description = Command([
        'xacro ', robot_xacro,
        ' can_iface:=', can_iface,
        ' robot_namespace:=', namespace,
    ])

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )


    # humble-and-earlier use cmd_vel_unstamped, jazzy-and-later use cmd_vel
    humble_unstamped = '_unstamped' if rosdistro <= 'humble' else ''

    # Twist mux
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        remappings={
            ('cmd_vel_joy', 'cmd_vel_joy' + humble_unstamped),
            ('cmd_vel_out', 'diff_drive_controller/cmd_vel' + humble_unstamped),
        },
        parameters=[
            PathJoinSubstitution([ad_r1m_control, 'config', 'twist_mux.yaml']),
            {'use_stamped': rosdistro >= 'jazzy'}
        ]
    )

    # ros2_control controller_manager
    robot_control_config = PathJoinSubstitution([
        ad_r1m_control, 'config', 'controllers.yaml'
    ])
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            robot_control_config,
            LaunchConfiguration('extra_control_params_file')
        ],
        remappings=[('~/robot_description', 'robot_description')],
        output='both'
    )

    spawners = []
    for spawn, extra_args in [
        ('joint_state_broadcaster', []),
        ('diff_drive_controller', []),
        ('forward_velocity_controller', ['--inactive'])
    ]:
        spawners.append(Node(
            package='controller_manager',
            executable='spawner',
            name=[spawn, '_spawner'],
            arguments=[
                spawn,
                '--controller-manager', 'controller_manager',
                *extra_args],
            output='both',
        ))

    return LaunchDescription([
        decl_namespace,
        decl_can_iface,
        decl_robot_xacro,
        decl_extra_control_params_file,
        rsp,
        twist_mux_node,
        controller_manager_node,
        *spawners
    ])
