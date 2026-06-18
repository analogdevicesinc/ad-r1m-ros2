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
    rpi_mode = LaunchConfiguration('rpi_mode').perform(context).lower() == 'true'

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
    # Based on research from:
    #   - Labbé & Michaud, 2024: RTAB-Map SLAM Library
    #   - Phan et al., 2023: Sensor Fusion for RTAB-Map
    #   - Muravyev & Yakovlev, 2022: RGB-D SLAM in Large Indoor Environments
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
        # Paper (Labbé 2024): WheelIMU achieves 0.07m ATE vs 4.61m pure visual
        'odom_sensor_sync': False,

        # Nav2 integration
        'use_action_for_goal': True,

        # 2D mode for differential drive robot
        'Reg/Strategy': '0',            # 0=Vis, 1=ICP, 2=VisICP
        'Reg/Force3DoF': 'true',        # Constrain to 2D plane

        # Grid/Map settings
        # CRITICAL: Disable ray tracing for narrow 70° FOV camera
        # Paper: "ray tracing can incorrectly clear obstacles when camera can't see them"
        'Grid/RayTracing': 'false',
        'Grid/3D': 'false',             # 2D occupancy grid
        'Grid/FromDepth': 'true',
        'Grid/RangeMax': '5.0',
        'Grid/RangeMin': '0.3',
        'Grid/CellSize': '0.05',
        'Grid/NormalsSegmentation': 'false',
        'Grid/MaxGroundHeight': str(max_ground_height),
        'Grid/MaxObstacleHeight': '0.5',
        'Grid/MaxGroundAngle': '45',

        # Optimizer (2D mode)
        'Optimizer/GravitySigma': '0',
        'Optimizer/Strategy': '2',      # GTSAM (best for multi-session)

        # Memory management (CRITICAL for RPi)
        # Muravyev 2022: RTAB-Map uses ~3.6GB RAM for 300m without limits
        'Rtabmap/MemoryThr': '300',     # Max nodes in working memory
        'Rtabmap/TimeThr': '700',       # Max processing time (ms)
        'Mem/ImagePreDecimation': '2',
        'Mem/ImagePostDecimation': '2',
        'Mem/STMSize': '30',            # Short-term memory for dynamic filtering
        'Mem/RehearsalSimilarity': '0.2',

        # Visual features
        'Vis/FeatureType': '6',         # ORB features (fast)
        'Vis/MaxFeatures': '200',
        'Kp/MaxFeatures': '100',        # Loop closure features
        'Vis/CorType': '0',             # Features matching
        'Rtabmap/DetectionRate': '2.0', # Phan 2023: higher rate improves quality

        # Loop closure (critical for 70° narrow FOV)
        'RGBD/ProximityBySpace': 'true',
        'RGBD/ProximityMaxGraphDepth': '50',
        'RGBD/AngularUpdate': '0.1',
        'RGBD/LinearUpdate': '0.1',
        'RGBD/OptimizeMaxError': '1.0',
        'RGBD/NeighborLinkRefining': 'true',
        'RGBD/LoopClosureReextractFeatures': 'true',
    }

    # RPi mode: more aggressive optimization
    # Kunchala 2026: RPi 4B runs RTAB-Map at 65-80% CPU
    if rpi_mode:
        parameters.update({
            'Vis/MaxFeatures': '150',           # Fewer features
            'Kp/MaxFeatures': '75',
            'Rtabmap/DetectionRate': '1.0',     # Slower detection
            'Rtabmap/MemoryThr': '200',         # Smaller working memory
            'Mem/ImagePreDecimation': '4',      # More aggressive decimation
            'Mem/ImagePostDecimation': '4',
            'RGBD/ProximityMaxGraphDepth': '30', # Limit graph search
            'RGBD/LoopClosureReextractFeatures': 'false',  # Save CPU
        })

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

    # Point cloud assembler for narrow FOV compensation
    # Paper (Labbé 2024): "The limited field of view of the front facing RGB-D camera was also a problem"
    # Accumulates scans over time to build wider coverage
    nodes.append(Node(
        condition=IfCondition(LaunchConfiguration('assemble_cloud')),
        package='rtabmap_util',
        executable='point_cloud_assembler',
        name='point_cloud_assembler',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'max_clouds': 20,           # Rolling buffer of 20 scans
            'assembling_time': 0.0,     # Use max_clouds instead of time
            'fixed_frame_id': odom_frame_id,
            'frame_id': frame_id,
            'voxel_size': 0.05,         # 5cm voxel grid
            'noise_filter_radius': 0.0, # Disabled
            'noise_filter_min_neighbors': 0,
            'circular_buffer': True,
        }],
        remappings=[
            ('cloud', cloud_topic),
            ('assembled_cloud', 'camera/assembled_cloud'),
        ],
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
            'assemble_cloud',
            default_value='false',
            description='Enable point cloud assembler for narrow FOV compensation'),

        DeclareLaunchArgument(
            'rpi_mode',
            default_value='false',
            description='Enable aggressive RPi optimization (lower features, slower rate)'),

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
