"""
Launch file for the AD-R1M IMU hardware-in-the-loop demo.

Brings up:
  1. robot_state_publisher   (URDF → TF + robot_description)
  2. Gazebo                  (sim world + spawn entity)
  3. ros2_control            (diff_drive_controller + joint_state_broadcaster)
  4. twist_mux               (with HIL channel at priority 45)
  5. robot_localization EKF   (wheel odom + sim IMU)
  6. imu_filter_madgwick      (/imu/data_raw → /imu/data with orientation)
  7. imu_hil_controller      (P-control: real IMU → sim yaw)
  8. RViz
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    # -- Resolved package paths --
    ad_r1m_examples = FindPackageShare('ad_r1m_examples')
    ad_r1m_gazebo = FindPackageShare('ad_r1m_gazebo')
    ad_r1m_description = FindPackageShare('ad_r1m_description')

    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')

    # ── Robot description ──
    # ParameterValue(…, value_type=str) prevents the launch system from
    # yaml-parsing the URDF XML, which corrupts it on Humble.
    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([ad_r1m_gazebo, 'urdf', 'ad_r1m_sim.urdf.xacro']),
            ' robot_namespace:=',
        ]),
        value_type=str,
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # ── Gazebo ──
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py',
        ])),
        launch_arguments={
            'params_file': PathJoinSubstitution([
                ad_r1m_gazebo, 'config', 'gazebo_params.yaml',
            ]),
            'world': world,
        }.items(),
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'ad_r1m'],
        output='screen',
    )

    # ── ros2_control controller spawners ──
    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller',
                   '--controller-manager', 'controller_manager'],
    )

    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager', 'controller_manager'],
    )

    # ── twist_mux (with HIL channel) ──
    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[
            PathJoinSubstitution([ad_r1m_examples, 'imu_hil_demo', 'config', 'twist_mux_hil.yaml']),
            {'use_sim_time': True},
        ],
        remappings=[('/cmd_vel_out', 'diff_drive_controller/cmd_vel_unstamped')],
    )

    # ── EKF (wheel odom + sim IMU) ──
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            PathJoinSubstitution([ad_r1m_examples, 'imu_hil_demo', 'config', 'hil_ekf.yaml']),
            {'use_sim_time': True},
        ],
    )

    # ── Madgwick filter (raw IMU angular vel → orientation quaternion) ──
    # Subscribes: /imu/data_raw  →  Publishes: /imu/data
    madgwick = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_madgwick_node',
        output='screen',
        parameters=[
            PathJoinSubstitution([ad_r1m_examples, 'imu_hil_demo', 'config', 'madgwick.yaml']),
        ],
        remappings=[
            ('imu/data_raw', '/camera1/imu'),
            ('imu/data', '/madgwick/imu'),
        ],
    )

    # ── HIL controller ──
    hil_controller = Node(
        package='ad_r1m_examples',
        executable='imu_hil_controller.py',
        name='imu_hil_controller',
        output='screen',
        prefix='xterm -e',
        parameters=[
            PathJoinSubstitution([ad_r1m_examples, 'imu_hil_demo', 'config', 'hil_params.yaml']),
            {'use_sim_time': True},
        ],
    )

    # ── RViz ──
    nodes = [
        rsp,
        gazebo,
        spawn_entity,
        diff_drive_spawner,
        joint_broad_spawner,
        twist_mux,
        ekf_node,
        madgwick,
        hil_controller,
    ]

    if use_rviz.perform(context).lower() == 'true':
        rviz = Node(
            package='rviz2',
            executable='rviz2',
            arguments=[
                '-d', PathJoinSubstitution([
                    ad_r1m_description, 'rviz', 'main_sim.rviz',
                ]),
            ],
            parameters=[{'use_sim_time': True}],
            output='screen',
        )
        nodes.append(rviz)

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_gazebo'), 'worlds', 'empty.world',
            ]),
            description='Path to Gazebo world file',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz alongside the simulation',
        ),
        OpaqueFunction(function=launch_setup),
    ])
