import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, IfElseSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    rosdistro = os.environ['ROS_DISTRO']
    ad_r1m_control = FindPackageShare('ad_r1m_control')

    decl_extra_control_params_file = DeclareLaunchArgument('extra_control_params_file', default_value='')
    decl_sensor_fusion = DeclareLaunchArgument('sensor_fusion', default_value='true')


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
    no_sensor_fusion_config = PathJoinSubstitution([
        ad_r1m_control, 'config', 'controllers_no_ekf.yaml'
    ])
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            robot_control_config,
            IfElseSubstitution(LaunchConfiguration('sensor_fusion'),
                               if_value='',
                               else_value=no_sensor_fusion_config),
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
        decl_extra_control_params_file,
        twist_mux_node,
        controller_manager_node,
        *spawners
    ])
