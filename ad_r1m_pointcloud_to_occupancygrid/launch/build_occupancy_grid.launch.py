from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'topic',
            description='a pointcloud topic to process',
            default_value='nonground'),
        Node(
            package='pointcloud_to_grid',
            executable='pointcloud_to_grid_node',
            output='screen',
            parameters=[
                {'cloud_in_topic': LaunchConfiguration('topic')},
                {'position_x': -5.0},
                {'position_y': 0.0},
                {'verbose1': False},
                {'verbose2': False},
                {'cell_size': 0.1},
                {'length_x': 40.0},
                {'length_y': 60.0},
                {'height_factor': 1.0},
                {'intensity_factor': 1.0},
                # {'frame_out': 'os1_sensor'},
                # OccupancyGrid topics
                {'mapi_topic_name': 'intensity_grid'},
                {'maph_topic_name': 'height_grid'},
                # GridMap topics
                {'mapi_gridmap_topic_name': 'intensity_gridmap'},
                {'maph_gridmap_topic_name': 'height_gridmap'},
                # Fitering parameters
                {'filter_enable': True},
                {'z_min': 0.0},
                {'z_max': 0.5},
                # Radius outlier removal
                {'ror_enable': True},
                {'ror_radius': 0.35},
                {'ror_min_neighbors_in_radius': 5},
                # Statistical outlier removal
                {'sor_enable': False},
                {'sor_mean': 30},
                {'sor_stddev_mul_thresh': 0.5},
                # Pass through filter (z-band)
                {'pass_enable': True},
                {'pass_z_min': 0.0},
                {'pass_z_max': 0.5},
                # Voxel grid
                {'voxel_enable': True},
                {'voxel_lx': 0.07},
                {'voxel_ly': 0.07},
                {'voxel_lz': 0.17},
                # Clustering
                {'cluster_enable': False},
                {'cluster_tolerance': 0.2},
                {'cluster_min_size': 10},
                {'cluster_max_size': 25000},
                # Gaussian mapping on z for intensity mapping
                {'gaussian_enable': True},
                {'gaussian_mean': 0.2},
                {'gaussian_stddev': 0.05},
                # Normal mean averaging of maps
                {'normal_averaging_enable': True},
                # Moving average parameters
                {'moving_average_enable': False},
                {'ma_alpha': 0.5},
            ]
        )
    ])
