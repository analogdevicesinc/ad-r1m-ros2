import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def launch_setup(context, *args, **kwargs):
    rs_config_path = LaunchConfiguration('config_path').perform(context)
    with open(rs_config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # cuVSLAM remapping list for sim mode
    cuVSLAM_remapping = [
        ('visual_slam/image_0', '/camera/infra1/image_raw'),
        ('visual_slam/camera_info_0', '/camera/infra1/camera_info'),
        ('visual_slam/image_1', '/camera/infra2/image_raw'),
        ('visual_slam/camera_info_1', '/camera/infra2/camera_info'),
        ('visual_slam/imu', '/camera/imu'),
    ]

    realsense_camera_node = Node(
        name='camera',
        namespace='camera',
        package='realsense2_camera',
        executable='realsense2_camera_node',
        parameters=[config['realsense2_params']],
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[config['visual_slam'], {'use_sim_time': True}],
        remappings=cuVSLAM_remapping,
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[visual_slam_node],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return [visual_slam_launch_container]
    # return [visual_slam_launch_container, realsense_camera_node]


def generate_launch_description():
    pkg_share = get_package_share_directory('ad_r1m_perception_cuvslam')

    config_path_arg = DeclareLaunchArgument(
        'config_path',
        default_value=os.path.join(pkg_share, 'config', 'cuvslam_single_realsense.yaml'),
        description='Path to the YAML configuration file'
    )

    return LaunchDescription([
        config_path_arg,
        OpaqueFunction(function=launch_setup),
    ])
