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
    use_amcl = LaunchConfiguration('amcl').perform(context).lower() == 'true'
    params_file_arg = LaunchConfiguration('params_file').perform(context)

    if params_file_arg:
        params_file = params_file_arg
    elif use_sim_time.perform(context).lower() == 'true':
        params_file = PathJoinSubstitution([FindPackageShare('ad_r1m_navigation'), 'config', 'nav2_params_sim.yaml'])
    else:
        params_file = PathJoinSubstitution([FindPackageShare('ad_r1m_navigation'), 'config', 'navigation_params.yaml'])

    lifecycle_nodes = ['map_server']
    if use_amcl:
        lifecycle_nodes.append('amcl')

    namespace_str = namespace.perform(context)

    remappings = []
    if namespace_str == '':
        remappings.append(('map', '/map'))

    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file}

    if namespace_str != '':
        param_substitutions['amcl.ros__parameters.odom_frame_id'] = f'{namespace_str}/odom'
        param_substitutions['amcl.ros__parameters.base_frame_id'] = f'{namespace_str}/base_link'

    configured_params = RewrittenYaml(
        source_file=params_file,  # type: ignore[arg-type]
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True)

    nodes = [
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params],
            namespace=namespace,
            remappings=remappings),
    ]

    if use_amcl:
        nodes.append(
            Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                parameters=[configured_params],
                namespace=namespace,
                remappings=remappings))

    nodes.append(
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}],
            namespace=namespace))

    return nodes


def generate_launch_description():
    pkg_dir = FindPackageShare('ad_r1m_navigation')

    return LaunchDescription([
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Top-level namespace'),

        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution([pkg_dir, 'maps', 'world.yaml']),
            description='Full path to map yaml file to load'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically startup the nav2 stack'),

        DeclareLaunchArgument(
            'params_file',
            default_value='',
            description='Full path to the ROS2 parameters file to use (auto-selected based on use_sim_time if not set)'),

        DeclareLaunchArgument(
            'amcl', default_value='true',
            description='Launch AMCL for localization'),

        OpaqueFunction(function=launch_setup)
    ])
