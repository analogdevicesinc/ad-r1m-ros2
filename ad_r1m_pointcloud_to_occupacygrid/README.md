# `ad_r1m_pointcloud_to_occupancygrid` ROS 2 package
This package converts `sensor_msgs/PointCloud2` data to both `nav_msgs/OccupancyGrid` and `grid_map_msgs/GridMap` 2D map data based on intensity and / or height.

<img src="doc/Map_build_sim_demo.gif" alt="Pointcloud to occupancy grid preview" width="800">

[![Static Badge](https://img.shields.io/badge/ROS_2-Humble-34aec5)](https://docs.ros.org/en/humble/)

## Build
```
cd ~/<your_ros_workspace>/src 
git clone https://github.com/analogdevicesinc/ad_r1m_ros2
cd ~/ros2_ws/ 
colcon build --packages-select ad_r1m_pointcloud_to_occupancygrid --symlink-install
```
Don't foget to `source ~/<your_ros_workspace>/install/setup.bash`. 


## Features
- Few dependencies (ROS 2, PCL, and grid_map_msgs mainly) [ROS installation](http://wiki.ros.org/ROS/Installation)
- **Dual output format support**: publishes both `nav_msgs/OccupancyGrid` and `grid_map_msgs/GridMap`
- **Additional pointcloud filtering**:
  - **Radius Outlier Removal** – removes isolated points that lack nearby neighbors.
  - **Statistical Outlier Removal** – eliminates noisy spikes based on neighborhood statistics.
  - **Pass-Through Z Filter** – keeps only points within a specified height range (useful for filtering floor/ceiling).
  - **Voxel Grid Downsampling** – reduces point density and computation by keeping one point per voxel.
  - **Clustering (optional)** – segments the cloud and allows ignoring very small or noisy clusters.
  - **Gaussian Z-Weighting** – weights points based on height using a Gaussian curve (mean ≈ robot mid-height, stddev ≈ half robot height) to suppress floor/ceiling noise in intensity mapping.
  - **Normal Mean Averaging** – maintains a cumulative average of all generated grids for stable maps in static environments.
  - **Moving Average Filtering** – exponential smoothing of consecutive maps to reduce noise while allowing gradual adaptation to dynamic environments.


# Getting started

Start the node in a **new terminal** :
```r
ros2 launch ad_r1m_pointcloud_to_grid build_occuupancy_grid.launch.py
```
Alternatively, start with subscribing to `/my_cloud_topic`:
```r
ros2 launch ad_r1m_pointcloud_to_grid build_occuupancy_grid.launch.py topic:=my_cloud_topic
```

Start the visualization in a **new terminal** :
```r
ros2 launch ad_r1m_pointcloud_to_occupancygrid rviz.launch.py
```

## Dual Output Format Support

The package supports publishing both `nav_msgs/OccupancyGrid` and `grid_map_msgs/GridMap` message types simultaneously. This allows for better integration with different ROS 2 packages that may prefer one format over the other.

### New Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mapi_gridmap_topic_name` | string | `intensity_gridmap` | Topic name for intensity GridMap |
| `maph_gridmap_topic_name` | string | `height_gridmap` | Topic name for height GridMap |
| `cell_size` | float | `0.5f` | Cell size (m) of each point's projection |
| `length_x` | float | `20.0f` | Map length (m) on X-axis |
| `length_y` | float | `30.0f` | Map length (m) on Y-axis |
| `filter_enable` | bool |  `true` | When true, individual filters (ROR, SOR, pass-through, voxel, etc.) follow their own enable/disable settings. <br>When false, all filters are forcibly disabled, regardless of any per-filter configuration. <br>Use this to quickly turn the entire filtering system on or off without modifying each filter parameter.|
| `z_min` | float | `-10000.0f` | Minimum height for 3D points (m) |
| `z_max` | float | `10000.0f` | Maximum height for 3D points (m) |
| `ror_enable` | bool | `true` | Enable/Disable Radius outlier removal (ROR) filter |
| `ror_radius` | float | `0.25f` | Search radius around each point (m) |
| `ror_min_neighbors_in_radius` | int | `5` | Minimum number of neighbors required within `ror_radius`.<br> Points with fewer neighbors are removed. |
| `sor_enable` | bool | `true` | Enable/Disable Statistical outlier removal (SOR) filter |
| `sor_mean` | int | `30` |  Number of nearest neighbors considered when evaluating local statistics |
| `sor_stddev_mul_thresh` | float | `0.5f` | Standard deviation multiplier.<br> Points whose distance exceeds mean+sor_stddev_mul_thresh*std_dev (m) are removed. |
| `pass_enable` | bool | `true` | Enable/Disable pass-through filter |
| `pass_z_min` | float | `0.0f` | Minimum Z value to keep (m) |
| `pass_z_max` | float | `2.0f` | Maximum Z value to keep (m) |
| `voxel_enable` | bool | `true` | Enable/Disable voxel-grid downsampling.<br> Reduces point count and enforces uniform density.|
| `voxel_lx` | float | `0.07f` | Leaf size in the X direction |
| `voxel_ly` | float | `0.07f` | Leaf size in the Y direction |
| `voxel_lz` | float | `0.07f` | Leaf size in the Z direction |
| `cluster_enable` | bool | `true` | Enable/Disable point clustering.<br> Used to isolate meaningful clusters of points and remove small noisy fragments. |
| `cluster_tolerance` | float | `0.2f` | Maximum distance (m) between neighboring points within the same cluster |
| `cluster_min_size` | int | `10` | Minimum number of points in a valid cluster |
| `cluster_max_size` | int | `25000` | Maximum number of points in a valid clusters |
| `gaussian_enable` | bool | `true` | Enables/Disables Gaussian weighting. <br> Each point is weighted based on how close its Z-value is to a Gaussian distribution. <br> Points near the robot’s obstacle-height zone contribute strongly, while floor/ceiling <br> points get down-weighted. |
| `gaussian_mean` | float | `0.2f` | Center height (m) of the Gaussian (typically robot mid-height) |
| `gaussian_stddev` | float | `0.05f` | Width (m) of the Gaussian (approx. half robot height recommended) |
| `normal_averaging_enable` | bool | `false` | Enable/Disable normal mean averaging over all maps produced so far.<br> Produces a stable long-term map in static environments|
| `moving_average_enable` | bool | `false` | Enable/Disable exponential moving average. <br> Suited for dynamic environments where old data should slowly fade out. |
| `ma_alpha` | float | `0.9f` | Smoothing factor [0, 1]. <br>`ma_alpha` close to 1 &rarr; fast reaction to new data.<br> `ma_alpha` close to 0 &rarr; slow smoothing of noise. |



### Output Topics

The node publishes to four topics simultaneously:

**OccupancyGrid format:**
- `intensity_grid` (`nav_msgs/OccupancyGrid`)
- `height_grid` (`nav_msgs/OccupancyGrid`)

**GridMap format:**
- `intensity_gridmap` (`grid_map_msgs/GridMap`)
- `height_gridmap` (`grid_map_msgs/GridMap`)

### Usage Example

```bash
# Launch with custom GridMap topic names
ros2 launch ad_r1m_pointcloud_to_occupancygrid build_occupancy_grid.launch.py topic:=my_pointcloud mapi_gridmap_topic_name:=my_intensity_map maph_gridmap_topic_name:=my_height_map
```

## QoS Configuration

The package is configured to use `BEST_EFFORT` reliability QoS policy for the input point cloud subscription. This ensures compatibility with typical LiDAR sensor publishers that often use this policy for performance reasons. This prevents QoS compatibility warnings that might appear with the default `RELIABLE` policy.


## Related solutions
- [https://github.com/jkk-research/pointcloud_to_grid/tree/ros2](https://github.com/jkk-research/pointcloud_to_grid/tree/ros2) - This is a ROS package used for occupancy grid and grid map building from raw LIDAR pointcloud data. Does not include pre-filtering options for the pointcloud.
- [github.com/ANYbotics/grid_map](https://github.com/ANYbotics/grid_map) - This is a C++ library with ROS interface to manage two-dimensional grid maps with multiple data layers. 
- [github.com/306327680/PointCloud-to-grid-map](https://github.com/306327680/PointCloud-to-grid-map) - A similar solution but instead PointCloud2 it uses PointCloud

## Remarks

In VS code it is advised to add the following to include path:

``` r
${workspaceFolder}/**
/opt/ros/humble/include/**
/usr/include/pcl-1.12/**
/usr/include/eigen3/**
```

If you are not sure where your header files are use e.g.:
``` r
find /usr/include -name point_cloud.h
find /usr/include -name crop_box.h
```