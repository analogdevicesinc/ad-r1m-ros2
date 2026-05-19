import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare
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

    urdf_file = PathJoinSubstitution([
        config_directory, 'urdf', 'realsense_calibration.urdf.xacro'
    ])
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    rs_config_path = PathJoinSubstitution([
        config_directory, 'config', 'vslam_multi_realsense.yaml'
    ])
    with open(rs_config_path, 'r') as rs_config_file:
        rs_config = yaml.safe_load(rs_config_file)

    remapping_list_cuVSLAM, optical_frames = [], []
    # list of image topics to be synchronized and topics to re-publish sync
    # camera data
    topics2subscribe, topics2publish = [], []

    # two physical cameras for each realsense device
    num_cameras = 2 * len(rs_config['cameras'])

    # Build remapping list for cuVSLAM subscription.
    # Build sync node parameter list: topics2subscribe, topics2publish
    for idx in range(num_cameras):
        infra_cnt = idx % 2 + 1
        camera_cnt = rs_config['cameras'][idx // 2]['camera_name']
        optical_frames += [f'{camera_cnt}_infra{infra_cnt}_optical_frame']
        remapping_list_cuVSLAM += [
            (f'visual_slam/image_{idx}',
             f'/sync/{camera_cnt}/infra{infra_cnt}/image_rect_raw'),
            (f'visual_slam/camera_info_{idx}',
             f'/sync/{camera_cnt}/infra{infra_cnt}/camera_info')]

        topics2subscribe += [f'/{camera_cnt}/infra{infra_cnt}/image_rect_raw',
                             f'/{camera_cnt}/infra{infra_cnt}/camera_info']
        topics2publish += [
            f'/sync/{camera_cnt}/infra{infra_cnt}/image_rect_raw',
            f'/sync/{camera_cnt}/infra{infra_cnt}/camera_info']

    def realsense_capture(common_params, camera_params):
        stereo_capture = ComposableNode(
            name=camera_params['camera_name'],
            namespace=camera_params['camera_name'],
            package='realsense2_camera',
            plugin='realsense2_camera::RealSenseNodeFactory',
            parameters=[common_params | camera_params]
        )
        return stereo_capture

    # TODO: add parameters for visual slam into YAML
    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': False,
            'rectified_images': True,
            'enable_imu_fusion': False,  # if only one camera is used, this can be set to true
            'image_jitter_threshold_ms': 300.00,
            'base_frame': 'base_link',
            'enable_slam_visualization': False,
            'enable_landmarks_view': False,
            'enable_observations_view': False,
            'enable_ground_constraint_in_odometry': False,
            'enable_ground_constraint_in_slam': False,
            'enable_localization_n_mapping': True,
            'enable_debug_mode': False,
            'num_cameras': num_cameras,
            'min_num_images': num_cameras,
            'camera_optical_frames': optical_frames
        }],
        remappings=remapping_list_cuVSLAM,
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=([visual_slam_node]),
        output='screen',
    )

    # TODO: include all realsense parameters in the config file
    realsense_image_capture = LoadComposableNodes(
        target_container='visual_slam_launch_container',
        composable_node_descriptions=([
            realsense_capture(rs_config['common_params'], camera_config)
            for camera_config in rs_config['cameras']
        ]),
    )

    # TODO: get sync params from yaml config file
    camera_sync_node = ComposableNode(
        name='realsense_image_sync',
        namespace='camera_sync',
        package='ad_r1m_perception_cuvslam',
        plugin='camera_sync::MultiApproxSync',
        parameters=[{'topics2subscribe': topics2subscribe,
                     'topics2publish': topics2publish,
                     'inter_message_slop': 0.001,  # in sec
                     'inner_message_slop': 0.001,  # in sec
                     }]
    )
    camera_sync_node_vslam_container = LoadComposableNodes(
        target_container='visual_slam_launch_container',
        composable_node_descriptions=([camera_sync_node]),
        output='screen',
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': robot_description}]
    )

    return LaunchDescription([
        use_rosbag_arg,
        foxglove_bridge_launch,
        state_publisher,
        realsense_image_capture,
        visual_slam_launch_container,
        camera_sync_node_vslam_container,
    ])
