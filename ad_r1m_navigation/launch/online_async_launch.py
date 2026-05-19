from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    namespace = LaunchConfiguration('namespace')

    namespace_str = namespace.perform(context)

    # Build param_substitutions based on namespace
    param_substitutions = {'use_sim_time': use_sim_time}

    if namespace_str != '':
        param_substitutions['odom_frame'] = f'{namespace_str}/odom'
        param_substitutions['base_frame'] = f'{namespace_str}/base_link'

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True)

    start_async_slam_toolbox_node = Node(
        parameters=[configured_params],
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace=namespace,
        output='screen')

    return [start_async_slam_toolbox_node]


def generate_launch_description():
    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock')
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('ad_r1m_navigation'),
            'config', 'mapper_params_online_async.yaml']),
        description='Full path to the ROS2 parameters file to use for the slam_toolbox node')
    declare_namespace_argument = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace for multi-robot systems (e.g., robot1, robot2)')

    log_config_file = LogInfo(msg=[
        'Using SLAM Toolbox config file: ', LaunchConfiguration('params_file')
    ])

    return LaunchDescription([
        declare_use_sim_time_argument,
        declare_params_file_cmd,
        declare_namespace_argument,
        log_config_file,
        OpaqueFunction(function=launch_setup)
    ])
