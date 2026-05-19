import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource


def generate_launch_description():
    use_rosbag_arg = DeclareLaunchArgument(
        'use_rosbag',
        default_value='False',
        description='Whether to execute rosbag'
    )
    use_rosbag = LaunchConfiguration('use_rosbag')

    config_directory = FindPackageShare('ad_r1m_perception_cuvslam')

    foxglove_xml_config = PathJoinSubstitution([
        config_directory, 'config', 'foxglove_bridge_launch.xml'
    ])
    foxglove_bridge_launch = IncludeLaunchDescription(
        XMLLaunchDescriptionSource([foxglove_xml_config])
    )

    # for multiple cameras use realsense_calibration.urdf.xacro
    urdf_file = PathJoinSubstitution([
        config_directory, 'urdf', 'single_realsense_calibration.urdf.xacro'
    ])
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # for multiple cameras use vslam_multi_realsense.yaml
    rs_config_path = PathJoinSubstitution([
        config_directory, 'config', 'vslam_single_realsense.yaml'
    ])
    with open(rs_config_path, 'r') as rs_config_file:
        rs_config = yaml.safe_load(rs_config_file)

    remapping_list, optical_frames = [], []
    # two physical cameras for each realsense device
    num_cameras = 2 * len(rs_config['cameras'])

    for idx in range(num_cameras):
        infra_cnt = idx % 2 + 1
        camera_cnt = rs_config['cameras'][idx // 2]['camera_name']
        optical_frames += [f'{camera_cnt}_infra{infra_cnt}_optical_frame']
        remapping_list += [(f'visual_slam/image_{idx}',
                            f'/{camera_cnt}/infra{infra_cnt}/image_rect_raw'),
                           (f'visual_slam/camera_info_{idx}',
                            f'/{camera_cnt}/infra{infra_cnt}/camera_info')]

    # This topic remap is useful for one camera (camera1) setup for imu fusion
    remapping_list += [(f'/visual_slam/imu', f'/camera1/imu')]

    def realsense_capture(common_params, camera_params):
        stereo_capture = ComposableNode(
            name=camera_params['camera_name'],
            namespace=camera_params['camera_name'],
            package='realsense2_camera',
            plugin='realsense2_camera::RealSenseNodeFactory',
            parameters=[common_params | camera_params]
        )
        return stereo_capture

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[
            rs_config['visual_slam'] |
            {'num_cameras': num_cameras,
             'min_num_images': num_cameras,
             'camera_optical_frames': optical_frames}
        ],
        remappings=remapping_list,
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=([visual_slam_node]),
        output='screen',
    )

    realsense_image_capture = LoadComposableNodes(
        target_container='visual_slam_launch_container',
        composable_node_descriptions=([
            realsense_capture(rs_config['common_params'], camera_config)
            for camera_config in rs_config['cameras']
        ]),
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        name='realsense_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )

    return LaunchDescription([
        use_rosbag_arg,
        # foxglove_bridge_launch,
        state_publisher,
        realsense_image_capture,
        visual_slam_launch_container
    ])
