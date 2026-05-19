import yaml

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    config_directory = FindPackageShare('ad_r1m_perception_cuvslam')

    rs_config_path = PathJoinSubstitution(
        [config_directory, 'config', 'cuvslam_single_realsense.yaml'])

    with open(rs_config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # cuVSLAM remapping list
    # cuVSLAM_remapping = [
    #     ('visual_slam/image_0', 'camera/infra1/image_rect_raw'),
    #     ('visual_slam/camera_info_0', 'camera/infra1/camera_info'),
    #     ('visual_slam/image_1', 'camera/infra2/image_rect_raw'),
    #     ('visual_slam/camera_info_1', 'camera/infra2/camera_info'),
    #     ('visual_slam/imu', 'camera/imu'),
    # ]

    # cuVSLAM remapping list for sim mode
    cuVSLAM_remapping = [
        ('visual_slam/image_0', '/camera/infra1/image_raw'),
        ('visual_slam/camera_info_0', '/camera/infra1/camera_info'),
        ('visual_slam/image_1', '/camera/infra2/image_raw'),
        ('visual_slam/camera_info_1', '/camera/infra2/camera_info'),
        ('visual_slam/imu', '/camera/imu'),
        # ('/camera/realsense_d435i_imu_plugin/out'),
    ]

    # Launch file which brings up visual slam node configured for RealSense.
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

    return LaunchDescription([visual_slam_launch_container])
    # return LaunchDescription([visual_slam_launch_container, realsense_camera_node])
    # return LaunchDescription([realsense_camera_node])
