"""
RTAB-Map ICP SLAM launch file for AD-R1M robot.

Point cloud only mode - uses ToF SDK point cloud directly.
Simpler pipeline: no image preprocessing needed.

Usage:
    # SLAM mode (mapping):
    ros2 launch ad_r1m_navigation rtabmap_icp_launch.py

    # Localization mode (use existing map):
    ros2 launch ad_r1m_navigation rtabmap_icp_launch.py localization:=true

    # With namespace (multi-robot):
    ros2 launch ad_r1m_navigation rtabmap_icp_launch.py namespace:=robot1
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

    namespace_str = namespace.perform(context)
    max_ground_height = LaunchConfiguration('max_ground_height').perform(context)
    rpi_mode = LaunchConfiguration('rpi_mode').perform(context).lower() == 'true'

    # Build frame IDs based on namespace
    if namespace_str != '':
        frame_id = f'{namespace_str}/base_link'
        odom_frame_id = f'{namespace_str}/odom'
        map_frame_id = 'map'
        cloud_topic = f'/{namespace_str}/cam1/point_cloud'
        odom_topic = f'/{namespace_str}/odometry/filtered'
        imu_topic = f'/{namespace_str}/imu'
    else:
        frame_id = 'base_link'
        odom_frame_id = 'odom'
        map_frame_id = 'map'
        cloud_topic = '/cam1/point_cloud'
        odom_topic = '/odometry/filtered'
        imu_topic = '/imu'

    # RTAB-Map ICP parameters
    # Based on research from:
    #   - Labbé & Michaud, 2024: RTAB-Map SLAM Library
    #   - Muravyev & Yakovlev, 2022: RGB-D SLAM in Large Indoor Environments
    # NOTE: Pure ICP can fail in corridors (low geometric complexity)
    # Paper shows WheelIMU→S2M achieves 0.07m ATE vs 4.61m pure S2M
    parameters = {
        # Frame configuration
        'frame_id': frame_id,
        'odom_frame_id': odom_frame_id,
        'map_frame_id': map_frame_id,
        'use_sim_time': use_sim_time,

        # Point cloud only mode
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_scan_cloud': True,
        'subscribe_odom_info': False,

        # Sync settings
        'approx_sync': True,
        'approx_sync_max_interval': 0.1,
        'topic_queue_size': 10,
        'sync_queue_size': 10,

        # Use external odometry (EKF-fused wheel + IMU)
        # CRITICAL: External odometry prevents ICP drift in corridors
        'odom_sensor_sync': False,

        # Nav2 integration
        'use_action_for_goal': True,

        # ICP Registration
        'Reg/Strategy': '1',        # 1=ICP (point cloud matching)
        'Reg/Force3DoF': 'true',    # Constrain to 2D plane

        # ICP parameters tuned for ToF
        'Icp/VoxelSize': '0.03',                # 3cm voxel downsample
        'Icp/MaxCorrespondenceDistance': '0.15', # 15cm max correspondence
        'Icp/PointToPlane': 'true',             # More robust registration
        'Icp/PointToPlaneK': '10',              # Neighbors for normal estimation
        'Icp/PointToPlaneRadius': '0.1',        # Radius for normal estimation
        'Icp/PointToPlaneMinComplexity': '0.02', # For corridor handling
        'Icp/Iterations': '30',                 # Max ICP iterations
        'Icp/Epsilon': '0.001',                 # Convergence threshold
        'Icp/MaxTranslation': '0.3',            # Max translation per iteration
        'Icp/MaxRotation': '0.5',               # Max rotation per iteration (rad)
        'Icp/CorrespondenceRatio': '0.2',       # Min ratio of correspondences
        'Icp/OutlierRatio': '0.7',              # Max outlier ratio
        'Icp/RangeMax': '4.0',                  # Max range (ToF effective range)
        'Icp/RangeMin': '0.2',                  # Min range (avoid near noise)
        'Icp/DownsamplingStep': '1',            # Use all points after voxel

        # Grid/Map settings
        # Disable ray tracing for narrow 70° FOV camera
        'Grid/RayTracing': 'false',
        'Grid/3D': 'false',
        'Grid/RangeMax': '4.0',
        'Grid/RangeMin': '0.2',
        'Grid/NormalsSegmentation': 'false',
        'Grid/MaxGroundHeight': str(max_ground_height),
        'Grid/MaxObstacleHeight': '0.5',
        'Grid/CellSize': '0.05',
        'Grid/ClusterRadius': '0.1',
        'Grid/MinClusterSize': '5',
        'Grid/FromDepth': 'false',              # Use scan_cloud, not depth
        'Grid/MaxGroundAngle': '45',

        # Optimizer (2D mode)
        'Optimizer/GravitySigma': '0',
        'Optimizer/Strategy': '2',              # GTSAM

        # Memory management (CRITICAL for RPi)
        'Rtabmap/MemoryThr': '300',
        'Rtabmap/TimeThr': '700',
        'Rtabmap/DetectionRate': '2.0',
        'Mem/STMSize': '30',
        'Mem/RehearsalSimilarity': '0.2',

        # Loop closure (proximity-based for ICP)
        'RGBD/ProximityBySpace': 'true',
        'RGBD/ProximityMaxGraphDepth': '50',
        'RGBD/ProximityPathMaxNeighbors': '10',
        'RGBD/AngularUpdate': '0.1',
        'RGBD/LinearUpdate': '0.1',
        'RGBD/OptimizeMaxError': '1.0',
        'RGBD/NeighborLinkRefining': 'true',
    }

    # RPi mode: more aggressive optimization
    if rpi_mode:
        parameters.update({
            'Rtabmap/DetectionRate': '1.0',
            'Rtabmap/MemoryThr': '200',
            'Icp/Iterations': '20',             # Fewer ICP iterations
            'Icp/VoxelSize': '0.05',            # Coarser voxels
            'RGBD/ProximityMaxGraphDepth': '30',
        })

    # Topic remappings for point cloud mode
    remappings = [
        ('scan_cloud', cloud_topic),
        ('odom', odom_topic),
        ('imu', imu_topic),
    ]

    nodes = []

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

    # RTAB-Map Visualization
    nodes.append(Node(
        condition=IfCondition(LaunchConfiguration('viz')),
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'frame_id': frame_id,
            'odom_frame_id': odom_frame_id,
            'subscribe_scan_cloud': True,
        }],
        remappings=remappings,
    ))

    # Obstacle detection for Nav2 local costmap
    nodes.append(Node(
        package='rtabmap_util',
        executable='obstacles_detection',
        name='obstacles_detection',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'frame_id': frame_id,
            'wait_for_transform': 0.2,
            'Grid/MaxGroundHeight': str(max_ground_height),
            'Grid/MaxObstacleHeight': '0.5',
            'Grid/NormalsSegmentation': 'false',
            'Grid/MinClusterSize': '10',
        }],
        remappings=[
            ('cloud', cloud_topic),
            ('obstacles', 'camera/obstacles'),
            ('ground', 'camera/ground'),
        ],
    ))

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'),

        DeclareLaunchArgument(
            'localization',
            default_value='false',
            description='Launch in localization mode'),

        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace'),

        DeclareLaunchArgument(
            'viz',
            default_value='true',
            description='Launch RTAB-Map visualization'),

        DeclareLaunchArgument(
            'max_ground_height',
            default_value='0.08',
            description='Max ground height in meters'),

        DeclareLaunchArgument(
            'rpi_mode',
            default_value='false',
            description='Enable aggressive RPi optimization'),

        LogInfo(msg=['Starting RTAB-Map ICP SLAM (point cloud only) for AD-R1M']),
        LogInfo(msg=['  Localization mode: ', LaunchConfiguration('localization')]),

        OpaqueFunction(function=launch_setup)
    ])
