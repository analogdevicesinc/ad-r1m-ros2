import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('ad_r1m_wander'), 'config', 'wander.yaml')
    rosdistro = os.environ.get('ROS_DISTRO', 'jazzy')

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='',
                              description='Robot namespace'),
        DeclareLaunchArgument('method', default_value='mean',
                              description='mean | min | percentile'),
        Node(
            package='ad_r1m_wander',
            executable='wander_node',
            name='wander',
            namespace=LaunchConfiguration('namespace'),
            output='screen',
            parameters=[
                config,
                {'use_stamped': rosdistro >= 'jazzy',
                 'method': LaunchConfiguration('method')},
            ],
        ),
    ])
