from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Check if we're told to use sim time
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Process the URDF file
    pkg_path = PathJoinSubstitution([
        FindPackageShare('ad_r1m_perception_cuvslam')])
    xacro_file = PathJoinSubstitution(
        [pkg_path, 'urdf', 'ad_r1m_realsense.urdf.xacro'])
    # robot_description_config = xacro.process_file(xacro_file).toxml()
    robot_description_config = Command([
        'xacro ', xacro_file,
        ' sim_mode:=', use_sim_time,
    ])

    # Create a robot_state_publisher node
    params = {
        'robot_description': robot_description_config,
        'use_sim_time': use_sim_time,
    }
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    # Launch!
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),

        node_robot_state_publisher
    ])
