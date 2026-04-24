from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = 'ad_r1m_pointcloud_to_occupancygrid'
    pkg_dir = FindPackageShare(pkg_name)

    return LaunchDescription([
        Node(
            package='rviz2',
            # namespace='',
            executable='rviz2',
            arguments=[
                '-d', PathJoinSubstitution([pkg_dir, 'doc', 'default.rviz']),
            ]
        )
    ])
