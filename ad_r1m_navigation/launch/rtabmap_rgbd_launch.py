"""
RTAB-Map RGBD SLAM launch file for AD-R1M robot.

Based on turtlebot3_rgbd demo, adapted for:
- ADI ToF camera (ADTF3175D) with depth + IR images
- IMU (ADIS16470)
- Wheel odometry (EKF-fused)
- Nav2 integration

Usage:
    # SLAM mode (mapping):
    ros2 launch ad_r1m_navigation rtabmap_rgbd_launch.py

    # Localization mode (use existing map):
    ros2 launch ad_r1m_navigation rtabmap_rgbd_launch.py localization:=true

    # With namespace (multi-robot):
    ros2 launch ad_r1m_navigation rtabmap_rgbd_launch.py namespace:=robot1
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    localization = LaunchConfiguration('localization')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')

    namespace_str = namespace.perform(context)
    max_ground_height = LaunchConfiguration('max_ground_height').perform(context)

    # Build frame IDs based on namespace
    if namespace_str != '':
        frame_id = f'{namespace_str}/base_link'
        odom_frame_id = f'{namespace_str}/odom'
        map_frame_id = 'map'
        camera_frame = f'{namespace_str}/cam1_adtf31xx_optical'
        # Topic prefixes
        depth_topic = f'/{namespace_str}/cam1/depth_image'
        rgb_topic = f'/{namespace_str}/cam1/ab_image'  # Amplitude image as grayscale
        camera_info_topic = f'/{namespace_str}/cam1/camera_info'
        cloud_topic = f'/{namespace_str}/cam1/point_cloud'
        odom_topic = f'/{namespace_str}/odometry/filtered'
        imu_topic = f'/{namespace_str}/imu'
    else:
        frame_id = 'base_link'
        odom_frame_id = 'odom'
        map_frame_id = 'map'
        camera_frame = 'cam1_adtf31xx_optical'
        # Topics without namespace
        depth_topic = '/cam1/depth_image'
        rgb_topic = '/cam1/ab_image'  # Amplitude image as grayscale
        camera_info_topic = '/cam1/camera_info'
        cloud_topic = '/cam1/point_cloud'
        odom_topic = '/odometry/filtered'
        imu_topic = '/imu'

    # RTAB-Map parameters
    parameters = {
        # Frame configuration
        'frame_id': frame_id,
        'odom_frame_id': odom_frame_id,
        'map_frame_id': map_frame_id,
        'use_sim_time': use_sim_time,

        # Subscription modes
        'subscribe_depth': True,
        'subscribe_rgb': True,
        'subscribe_odom_info': False,
        'approx_sync': True,
        'approx_sync_max_interval': 0.1,  # 100ms tolerance for sync
        'topic_queue_size': 30,           # Larger queue for preprocessing delay
        'sync_queue_size': 30,

        # Use external odometry (EKF-fused wheel + IMU)
        'odom_sensor_sync': False,

        # Nav2 integration
        'use_action_for_goal': True,

        # 2D mode for differential drive robot
        'Reg/Strategy': '0',            # 0=Vis, 1=ICP, 2=VisICP
        'Reg/Force3DoF': 'true',        # Constrain to 2D plane

        # Grid/Map settings
        'Grid/RayTracing': 'true',      # Fill empty space
        'Grid/3D': 'false',             # 2D occupancy grid
        'Grid/RangeMax': '5.0',         # Max range for mapping
        'Grid/NormalsSegmentation': 'false',
        'Grid/MaxGroundHeight': str(max_ground_height),
        'Grid/MaxObstacleHeight': '0.5',

        # Disable IMU gravity constraints (we're in 2D)
        'Optimizer/GravitySigma': '0',

        # Memory/Performance settings (tune for RPi)
        'Mem/ImagePreDecimation': '2',
        'Mem/ImagePostDecimation': '2',
        'Vis/MaxFeatures': '200',
        'Rtabmap/DetectionRate': '1.0',

        # Visual features
        'Vis/FeatureType': '6',         # ORB features (fast)
        'Vis/CorType': '0',             # Features matching
    }

    # Topic remappings for AD-R1M ToF camera
    remappings = [
        ('rgb/image', rgb_topic),
        ('rgb/camera_info', camera_info_topic),
        ('depth/image', depth_topic),
        ('odom', odom_topic),
        ('imu', imu_topic),
    ]

    nodes = []

    # ========================================
    # Image preprocessing for upside-down camera
    # Using combined preprocess node for lower latency
    # ========================================

    # Processed topic names
    depth_topic_processed = '/cam1/depth_image_processed' if namespace_str == '' else f'/{namespace_str}/cam1/depth_image_processed'
    rgb_topic_processed = '/cam1/ab_image_processed' if namespace_str == '' else f'/{namespace_str}/cam1/ab_image_processed'

    # Preprocess depth image: flip vertically
    nodes.append(Node(
        package='ad_r1m_navigation',
        executable='image_preprocess.py',
        name='depth_preprocess',
        namespace=namespace,
        output='screen',
        parameters=[{
            'input_topic': depth_topic,
            'output_topic': depth_topic_processed,
            'flip_vertical': True,
            'target_encoding': '',  # Keep 16UC1 for depth
        }],
    ))

    # Preprocess ab_image: flip vertically + fix encoding (16UC1 -> mono16)
    nodes.append(Node(
        package='ad_r1m_navigation',
        executable='image_preprocess.py',
        name='ab_preprocess',
        namespace=namespace,
        output='screen',
        parameters=[{
            'input_topic': rgb_topic,
            'output_topic': rgb_topic_processed,
            'flip_vertical': True,
            'target_encoding': 'mono16',  # Fix encoding for RTAB-Map
        }],
    ))

    # Update remappings with processed topics
    remappings = [
        ('rgb/image', rgb_topic_processed),
        ('rgb/camera_info', camera_info_topic),
        ('depth/image', depth_topic_processed),
        ('odom', odom_topic),
        ('imu', imu_topic),
    ]

    # SLAM Mode
    nodes.append(Node(
        condition=UnlessCondition(localization),
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        namespace=namespace,
        output='screen',
        parameters=[parameters],
        remappings=remappings,
        arguments=['-d'],  # Delete previous database on start
    ))

    # Localization Mode
    nodes.append(Node(
        condition=IfCondition(localization),
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        namespace=namespace,
        output='screen',
        parameters=[
            parameters,
            {
                'Mem/IncrementalMemory': 'False',
                'Mem/InitWMWithAllNodes': 'True',
            }
        ],
        remappings=remappings,
    ))

    # RTAB-Map Visualization (optional, disable for headless/RPi)
    nodes.append(Node(
        condition=IfCondition(LaunchConfiguration('viz')),
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        namespace=namespace,
        output='screen',
        parameters=[parameters],
        remappings=remappings,
    ))

    # Obstacle detection for Nav2 local costmap
    # Use ToF SDK point cloud directly (already correctly oriented)
    # Swap outputs because TF height classification is inverted for this camera mounting
    nodes.append(Node(
        package='rtabmap_util',
        executable='obstacles_detection',
        name='obstacles_detection',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'frame_id': frame_id,  # base_link
            'wait_for_transform': 0.2,
            'Grid/MaxGroundHeight': str(max_ground_height),
            'Grid/MaxObstacleHeight': '0.5',
            'Grid/NormalsSegmentation': 'false',
            'Grid/MinClusterSize': '10',
        }],
        remappings=[
            ('cloud', cloud_topic),  # /cam1/point_cloud (correct orientation)
            # Swap outputs to fix inverted height classification
            ('obstacles', 'camera/ground'),
            ('ground', 'camera/obstacles'),
        ],
    ))

    return nodes


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'localization',
            default_value='false',
            description='Launch in localization mode (use existing map)'),

        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace for multi-robot systems'),

        DeclareLaunchArgument(
            'viz',
            default_value='true',
            description='Launch RTAB-Map visualization (disable for headless/RPi)'),

        DeclareLaunchArgument(
            'max_ground_height',
            default_value='0.05',
            description='Maximum ground height in meters (above this is obstacle)'),

        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_navigation'),
                'config', 'rtabmap_params.yaml']),
            description='Full path to RTAB-Map parameters file'),

        LogInfo(msg=['Starting RTAB-Map RGBD SLAM for AD-R1M']),
        LogInfo(msg=['  Localization mode: ', LaunchConfiguration('localization')]),
        LogInfo(msg=['  Namespace: ', LaunchConfiguration('namespace')]),

        OpaqueFunction(function=launch_setup)
    ])
