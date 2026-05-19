from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    ad_r1m_gazebo = FindPackageShare('ad_r1m_gazebo')
    ad_r1m_control = FindPackageShare('ad_r1m_control')
    ad_r1m_description = FindPackageShare('ad_r1m_description')
    namespace = LaunchConfiguration('namespace')
    namespace_str = namespace.perform(context)
    world = LaunchConfiguration('world')

    robot_description = Command([
        'xacro ', PathJoinSubstitution([
            ad_r1m_gazebo, 'urdf', 'ad_r1m_sim.urdf.xacro']),
        ' robot_namespace:=', namespace,
    ])

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
        }]
    )

    twist_mux_params = PathJoinSubstitution(
        [ad_r1m_control, 'config', 'twist_mux.yaml'])
    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        namespace=namespace_str if namespace_str else None,
        parameters=[twist_mux_params, {'use_sim_time': True}],
        remappings=[
            ('/cmd_vel_out', 'diff_drive_controller/cmd_vel_unstamped')]
    )

    teleop_twist_keyboard = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [ad_r1m_gazebo, 'launch', 'teleopt.launch.py'])),
        launch_arguments={
            'use_sim_time': 'true',
            'namespace': namespace_str,
        }.items()
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])),
        launch_arguments={
            'params_file': PathJoinSubstitution([
                ad_r1m_gazebo, 'config', 'gazebo_params.yaml']),
            'world': world
        }.items()
    )

    robot_description_topic = f'/{namespace_str}/robot_description' if namespace_str else 'robot_description'

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', robot_description_topic,
                                   '-entity', 'ad_r1m'],
                        output='screen')
    print('Gazebo has started')

    # Controller manager configuration
    controller_manager_name = f'{namespace_str}/controller_manager' if namespace_str else 'controller_manager'

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller',
                   '--controller-manager', controller_manager_name],
    )

    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager', controller_manager_name],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        namespace=namespace_str if namespace_str else None,
        arguments=[
            '-d', PathJoinSubstitution([
                ad_r1m_description, 'rviz', 'main_sim.rviz']),
        ],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        namespace=namespace_str if namespace_str else None,
        output='screen',
        parameters=[
            PathJoinSubstitution([ad_r1m_control, 'config', 'ekf.yaml']),
            {'use_sim_time': True}
        ]
    )

    return [
        rsp,
        twist_mux,
        teleop_twist_keyboard,
        gazebo,
        spawn_entity,
        diff_drive_spawner,
        joint_broad_spawner,
        robot_localization_node,
        rviz,
    ]


def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Namespace for the robot'
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([
            FindPackageShare('ad_r1m_gazebo'), 'worlds', 'empty.world']),
        description='Path to world file'
    )


    return LaunchDescription([
        namespace_arg,
        world_arg,
        OpaqueFunction(function=launch_setup)
    ])
