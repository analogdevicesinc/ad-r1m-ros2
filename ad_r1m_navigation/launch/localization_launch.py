from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration('namespace')
    map_yaml_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    lifecycle_nodes = ['map_server', 'amcl']

    namespace_str = namespace.perform(context)

    remappings = []
    if namespace_str == '':
        remappings.append(('map', '/map'))

    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file}

    if namespace_str != '':
        param_substitutions['amcl.ros__parameters.odom_frame_id'] = f'{namespace_str}/odom'
        param_substitutions['amcl.ros__parameters.base_frame_id'] = f'{namespace_str}/base_link'

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True)

    return [
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params],
            namespace=namespace,
            remappings=remappings),

        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[configured_params],
            namespace=namespace,
            remappings=remappings),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}],
            namespace=namespace)
    ]


def generate_launch_description():
    # Get the launch directory
    pkg_dir = FindPackageShare('ad_r1m_navigation')

    return LaunchDescription([
        # Set env var to print messages to stdout immediately
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Top-level namespace'),

        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution([pkg_dir, 'maps', 'map.yaml']),
            description='Full path to map yaml file to load'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically startup the nav2 stack'),

        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution(
                [pkg_dir, 'config', 'nav2_params_sim.yaml']),
            description='Full path to the ROS2 parameters file to use'),

        OpaqueFunction(function=launch_setup)
    ])
