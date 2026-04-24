// ROS
#include "grid_map_msgs/msg/grid_map.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
// PCL
#include <iterator>
#include <pcl/filters/crop_box.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/passthrough.h>
#include <pcl/filters/radius_outlier_removal.h>
#include <pcl/filters/statistical_outlier_removal.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/search/kdtree.h>
#include <pcl/segmentation/extract_clusters.h>
#include <pcl_conversions/pcl_conversions.h>
// ROS package
#include <pointcloud_to_grid/pointcloud_to_grid_core.hpp>
// c++
#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <memory>
#include <string>
#include <vector>

class PointCloudToGrid : public rclcpp::Node {
  rcl_interfaces::msg::SetParametersResult
  parametersCallback(const std::vector<rclcpp::Parameter> &parameters) {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;
    result.reason = "success";

    for (const auto &param : parameters) {
      const auto &name = param.get_name();
      RCLCPP_INFO_STREAM(this->get_logger(),
                         "Param update: " << name << ": "
                                          << param.value_to_string());

      if (name == "mapi_topic_name") {
        grid_map.mapi_topic_name = param.as_string();
        pub_igrid = this->create_publisher<nav_msgs::msg::OccupancyGrid>(
            grid_map.mapi_topic_name, 10);
      } else if (name == "maph_topic_name") {
        grid_map.maph_topic_name = param.as_string();
        pub_hgrid = this->create_publisher<nav_msgs::msg::OccupancyGrid>(
            grid_map.maph_topic_name, 10);
      } else if (name == "mapi_gridmap_topic_name") {
        grid_map.mapi_gridmap_topic_name = param.as_string();
        pub_igridmap = this->create_publisher<grid_map_msgs::msg::GridMap>(
            grid_map.mapi_gridmap_topic_name, 10);
      } else if (name == "maph_gridmap_topic_name") {
        grid_map.maph_gridmap_topic_name = param.as_string();
        pub_hgridmap = this->create_publisher<grid_map_msgs::msg::GridMap>(
            grid_map.maph_gridmap_topic_name, 10);
      } else if (name == "cloud_in_topic") {
        cloud_in_topic = param.as_string();
        auto sensor_qos =
            rclcpp::QoS(10).reliability(RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT);
        sub_pc2_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            cloud_in_topic, sensor_qos,
            std::bind(&PointCloudToGrid::occupancy_grid_callback, this,
                      std::placeholders::_1));
      } else if (name == "cell_size") {
        grid_map.cell_size = param.as_double();
      } else if (name == "position_x") {
        grid_map.position_x = param.as_double();
      } else if (name == "position_y") {
        grid_map.position_y = param.as_double();
      } else if (name == "length_x") {
        grid_map.length_x = param.as_double();
      } else if (name == "length_y") {
        grid_map.length_y = param.as_double();
      } else if (name == "intensity_factor") {
        grid_map.intensity_factor = param.as_double();
      } else if (name == "height_factor") {
        grid_map.height_factor = param.as_double();
      } else if (name == "verbose1") {
        verbose1 = param.as_bool();
      } else if (name == "verbose2") {
        verbose2 = param.as_bool();
      } else if (name == "z_min") {
        grid_map.filter.z_min = param.as_double();
      } else if (name == "z_max") {
        grid_map.filter.z_max = param.as_double();
      } else if (name == "ror_enable") {
        grid_map.filter.ror_enable = param.as_bool();
      } else if (name == "ror_radius") {
        grid_map.filter.ror_radius = param.as_double();
      } else if (name == "ror_min_neighbors_in_radius") {
        grid_map.filter.ror_min_neighbors_in_radius =
            static_cast<unsigned int>(param.as_int());
      } else if (name == "sor_enable") {
        grid_map.filter.sor_enable = param.as_bool();
      } else if (name == "sor_mean") {
        grid_map.filter.sor_mean = static_cast<float>(param.as_double());
      } else if (name == "sor_stddev_mul_thresh") {
        grid_map.filter.sor_stddev_mul_thresh = param.as_double();
      } else if (name == "pass_enable") {
        grid_map.filter.pass_enable = param.as_bool();
      } else if (name == "pass_z_min") {
        grid_map.filter.pass_z_min = param.as_double();
      } else if (name == "pass_z_max") {
        grid_map.filter.pass_z_max = param.as_double();
      } else if (name == "voxel_enable") {
        grid_map.filter.voxel_enable = param.as_bool();
      } else if (name == "voxel_lx") {
        grid_map.filter.voxel_lx = param.as_double();
      } else if (name == "voxel_ly") {
        grid_map.filter.voxel_ly = param.as_double();
      } else if (name == "voxel_lz") {
        grid_map.filter.voxel_lz = param.as_double();
      } else if (name == "cluster_enable") {
        grid_map.filter.cluster_enable = param.as_bool();
      } else if (name == "cluster_tolerance") {
        grid_map.filter.cluster_tolerance = param.as_double();
      } else if (name == "cluster_min_size") {
        grid_map.filter.cluster_min_size =
            static_cast<unsigned int>(param.as_int());
      } else if (name == "cluster_max_size") {
        grid_map.filter.cluster_max_size =
            static_cast<unsigned int>(param.as_int());
      } else if (name == "gaussian_enable") {
        grid_map.filter.gaussian_enable = param.as_bool();
      } else if (name == "gaussian_mean") {
        grid_map.filter.gaussian_mean = param.as_double();
      } else if (name == "gaussian_stddev") {
        grid_map.filter.gaussian_stddev = param.as_double();
      } else if (name == "normal_averaging_enable") {
        grid_map.filter.normal_averaging_enable = param.as_bool();
      } else if (name == "moving_average_enable") {
        grid_map.filter.moving_average_enable = param.as_bool();
      } else if (name == "ma_alpha") {
        grid_map.filter.ma_alpha = param.as_double();
      }
    }

    grid_map.paramRefresh();
    return result;
  }

public:
  PointCloudToGrid() : Node("pointcloud_to_grid_node"), count_(0) {
    this->declare_parameter<std::string>("mapi_topic_name", "intensity_grid");
    this->declare_parameter<std::string>("maph_topic_name", "height_grid");
    this->declare_parameter<std::string>("mapi_gridmap_topic_name",
                                         "intensity_gridmap");
    this->declare_parameter<std::string>("maph_gridmap_topic_name",
                                         "height_gridmap");
    this->declare_parameter<std::string>("cloud_in_topic", cloud_in_topic);
    this->declare_parameter<float>("cell_size", 0.5);
    this->declare_parameter<float>("position_x", 0.0);
    this->declare_parameter<float>("position_y", 0.0);
    this->declare_parameter<float>("length_x", 20.0);
    this->declare_parameter<float>("length_y", 30.0);
    this->declare_parameter<float>("intensity_factor", 1.0);
    this->declare_parameter<float>("height_factor", 1.0);
    this->declare_parameter<bool>("verbose1", verbose1);
    this->declare_parameter<bool>("verbose2", verbose2);
    // Filtering parameters
    this->declare_parameter<bool>("filter_enable", true);
    this->declare_parameter<float>("z_min",
                                   -10000.0f); // minimum height for 3D points
    this->declare_parameter<float>("z_max",
                                   10000.0f); // maximum height for 3D points
    // Radius outlier removal
    this->declare_parameter<bool>("ror_enable", true);
    this->declare_parameter<float>("ror_radius", 0.25f);
    this->declare_parameter<int>("ror_min_neighbors_in_radius", 5);
    // Statistical outlier removal
    this->declare_parameter<bool>("sor_enable", true);
    this->declare_parameter<double>("sor_mean", 30.0);
    this->declare_parameter<double>("sor_stddev_mul_thresh", 0.5);
    // Pass through filter (z-band filter): same meaning
    // as z_min and z_max but soome redundancy never hurt
    // nobody
    this->declare_parameter<bool>("pass_enable", true);
    this->declare_parameter<float>("pass_z_min", 0.0f);
    this->declare_parameter<float>("pass_z_max", 2.0f);
    // Voxel grid
    this->declare_parameter<bool>("voxel_enable", true);
    this->declare_parameter<float>("voxel_lx", 0.07f);
    this->declare_parameter<float>("voxel_ly", 0.07f);
    this->declare_parameter<float>("voxel_lz", 0.07f);
    // Clustering: keeping only clusters in which points
    // are at least cluster_tolerance [m] to each others
    this->declare_parameter<bool>("cluster_enable", true);
    this->declare_parameter<float>("cluster_tolerance", 0.2);
    this->declare_parameter<int>("cluster_min_size", 10);
    this->declare_parameter<int>("cluster_max_size", 25000);
    // Gaussian mapping on z for intensity mapping
    this->declare_parameter<bool>("gaussian_enable", true);
    this->declare_parameter<float>("gaussian_mean", 0.2f);
    this->declare_parameter<float>("gaussian_stddev", 0.05f);
    // Normal mean averaging of maps
    this->declare_parameter<bool>("normal_averaging_enable", false);
    // Moving average parameters
    this->declare_parameter<bool>("moving_average_enable", false);
    this->declare_parameter<float>("ma_alpha", 0.9f);

    this->get_parameter("mapi_topic_name", grid_map.mapi_topic_name);
    this->get_parameter("maph_topic_name", grid_map.maph_topic_name);
    this->get_parameter("mapi_gridmap_topic_name",
                        grid_map.mapi_gridmap_topic_name);
    this->get_parameter("maph_gridmap_topic_name",
                        grid_map.maph_gridmap_topic_name);
    this->get_parameter("cloud_in_topic", cloud_in_topic);
    this->get_parameter("cell_size", grid_map.cell_size);
    this->get_parameter("position_x", grid_map.position_x);
    this->get_parameter("position_y", grid_map.position_y);
    this->get_parameter("length_x", grid_map.length_x);
    this->get_parameter("length_y", grid_map.length_y);
    this->get_parameter("intensity_factor", grid_map.intensity_factor);
    this->get_parameter("height_factor", grid_map.height_factor);
    this->get_parameter("verbose1", verbose1);
    this->get_parameter("verbose2", verbose2);
    // Filtering parameters
    this->get_parameter("filter_enable", grid_map.filter.filter_enable);
    this->get_parameter("z_min", grid_map.filter.z_min);
    this->get_parameter("z_max", grid_map.filter.z_max);
    // Radius outlier removal
    this->get_parameter("ror_enable", grid_map.filter.ror_enable);
    this->get_parameter("ror_radius", grid_map.filter.ror_radius);
    this->get_parameter("ror_min_neighbors_in_radius",
                        grid_map.filter.ror_min_neighbors_in_radius);
    // Statistical outlier removal
    this->get_parameter("sor_enable", grid_map.filter.sor_enable);
    this->get_parameter("sor_mean", grid_map.filter.sor_mean);
    this->get_parameter("sor_stddev_mul_thresh",
                        grid_map.filter.sor_stddev_mul_thresh);
    // Pass through filter (z-band filter): same meaning
    // as z_min and z_max but soome redundancy never hurt
    // nobody
    this->get_parameter("pass_enable", grid_map.filter.pass_enable);
    this->get_parameter("pass_z_min", grid_map.filter.pass_z_min);
    this->get_parameter("pass_z_max", grid_map.filter.pass_z_max);
    // Voxel grid
    this->get_parameter("voxel_enable", grid_map.filter.voxel_enable);
    this->get_parameter("voxel_lx", grid_map.filter.voxel_lx);
    this->get_parameter("voxel_ly", grid_map.filter.voxel_ly);
    this->get_parameter("voxel_lz", grid_map.filter.voxel_lz);
    // Clustering: keeping only clusters in which points
    // are at least cluster_tolerance [m] to each others
    this->get_parameter("cluster_enable", grid_map.filter.cluster_enable);
    this->get_parameter("cluster_tolerance", grid_map.filter.cluster_tolerance);
    this->get_parameter("cluster_min_size", grid_map.filter.cluster_min_size);
    this->get_parameter("cluster_max_size", grid_map.filter.cluster_max_size);
    // Gaussian mapping on z for intensity mapping
    this->get_parameter("gaussian_enable", grid_map.filter.gaussian_enable);
    this->get_parameter("gaussian_mean", grid_map.filter.gaussian_mean);
    this->get_parameter("gaussian_stddev", grid_map.filter.gaussian_stddev);
    // Normal mean averaging of maps
    this->get_parameter("normal_averaging_enable",
                        grid_map.filter.normal_averaging_enable);
    // Moving average parameters
    this->get_parameter("moving_average_enable",
                        grid_map.filter.moving_average_enable);
    this->get_parameter("ma_alpha", grid_map.filter.ma_alpha);

    grid_map.paramRefresh();

    pub_igrid = this->create_publisher<nav_msgs::msg::OccupancyGrid>(
        grid_map.mapi_topic_name, 10);
    pub_hgrid = this->create_publisher<nav_msgs::msg::OccupancyGrid>(
        grid_map.maph_topic_name, 10);
    pub_igridmap = this->create_publisher<grid_map_msgs::msg::GridMap>(
        grid_map.mapi_gridmap_topic_name, 10);
    pub_hgridmap = this->create_publisher<grid_map_msgs::msg::GridMap>(
        grid_map.maph_gridmap_topic_name, 10);

    avg_ipoints.assign(grid_map.cell_num_x * grid_map.cell_num_y, 0.0);

    // Configure QoS for sensor data - use BEST_EFFORT
    // reliability to match typical sensor publishers
    auto sensor_qos =
        rclcpp::QoS(10).reliability(RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT);
    sub_pc2_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        cloud_in_topic, sensor_qos,
        std::bind(&PointCloudToGrid::occupancy_grid_callback, this,
                  std::placeholders::_1));
    callback_handle_ = this->add_on_set_parameters_callback(std::bind(
        &PointCloudToGrid::parametersCallback, this, std::placeholders::_1));

    // Displaying current configuration at startup
    RCLCPP_INFO_STREAM(this->get_logger(),
                       "pointcloud_to_grid_node has been started.");
    RCLCPP_INFO_STREAM(this->get_logger(),
                       "Subscribing to: " << cloud_in_topic.c_str());
    RCLCPP_INFO_STREAM(this->get_logger(),
                       "Publishing to: " << grid_map.mapi_topic_name.c_str()
                                         << " and "
                                         << grid_map.maph_topic_name.c_str());
    RCLCPP_INFO_STREAM(this->get_logger(),
                       "Publishing GridMaps to: "
                           << grid_map.mapi_gridmap_topic_name.c_str()
                           << " and "
                           << grid_map.maph_gridmap_topic_name.c_str());

    RCLCPP_INFO_STREAM(this->get_logger(),
                       "Grid parameters: \n\t position_x: "
                           << grid_map.position_x
                           << "\n\t position_y: " << grid_map.position_y
                           << ",\n\t length_x: " << grid_map.length_x
                           << ",\n\t length_y: " << grid_map.length_y
                           << ",\n\t cell_size: " << grid_map.cell_size);

    RCLCPP_INFO_STREAM(this->get_logger(),
                       "\n Master filter enable: "
                           << (grid_map.filter.filter_enable ? "true" : "false")
                           << "\nIgnoring 3D points outside: \n\t z_min: "
                           << grid_map.filter.z_min
                           << ",\n\t z_max: " << grid_map.filter.z_max);

    RCLCPP_INFO_STREAM(
        this->get_logger(),
        "Filtering parameters: \n\t ROR:\n\t\t enable: "
            << (grid_map.filter.ror_enable ? "true" : "false")
            << ",\n\t\t radius: " << grid_map.filter.ror_radius
            << ",\n\t\t min_neighbors_in_radius: "
            << grid_map.filter.ror_min_neighbors_in_radius
            << ";\n\t SOR:\n\t\t enable:"
            << (grid_map.filter.sor_enable ? "true" : "false")
            << ",\n\t\t mean_k: " << grid_map.filter.sor_mean
            << ",\n\t\t stddev_mul_thresh: "
            << grid_map.filter.sor_stddev_mul_thresh
            << ";\n\t PassThrough:\n\t\t enable: "
            << (grid_map.filter.pass_enable ? "true" : "false")
            << ",\n\t\t z_min: " << grid_map.filter.pass_z_min
            << ",\n\t\t z_max: " << grid_map.filter.pass_z_max
            << ";\n\t VoxelGrid:\n\t\t enable: "
            << (grid_map.filter.voxel_enable ? "true" : "false")
            << ",\n\t\t lx: " << grid_map.filter.voxel_lx
            << ",\n\t\t ly: " << grid_map.filter.voxel_ly << ",\n\t\t lz: "
            << grid_map.filter.voxel_lz << ";\n\t Clustering:\n\t\t enable: "
            << (grid_map.filter.cluster_enable ? "true" : "false")
            << ",\n\t\t tolerance: " << grid_map.filter.cluster_tolerance
            << ",\n\t\t min_size: " << grid_map.filter.cluster_min_size
            << ",\n\t\t max_size: " << grid_map.filter.cluster_max_size
            << "\n\t Gaussian mapping:\n\t\t enable: "
            << (grid_map.filter.gaussian_enable ? "true" : "false")
            << ",\n\t\t mean: " << grid_map.filter.gaussian_mean
            << ",\n\t\t stddev: " << grid_map.filter.gaussian_stddev);

    RCLCPP_INFO_STREAM(
        this->get_logger(),
        "Averaging parameters: \n\t Normal mean averaging enable: "
            << (grid_map.filter.normal_averaging_enable ? "true" : "false")
            << "\n\t Moving average enable: "
            << (grid_map.filter.moving_average_enable ? "true" : "false")
            << ",\n\t\t ma_alpha: " << grid_map.filter.ma_alpha);
  }

private:
  // Method for recursively average intentity maps
  void update_normal_average(std::vector<float> &ipoints,
                             float &normal_avg_count) {
    normal_avg_count += 1.0;
    std::transform(avg_ipoints.begin(), avg_ipoints.end(), ipoints.begin(),
                   avg_ipoints.begin(),
                   [n = static_cast<float>(normal_avg_count)](
                       float old_val, float new_val) -> float {
                     return old_val + (new_val - old_val) / n;
                   });
  }

  // Method for averaging intensity maps using moving average
  void update_moving_average(std::vector<float> &ipoints, float alpha) {
    std::transform(avg_ipoints.begin(), avg_ipoints.end(), ipoints.begin(),
                   avg_ipoints.begin(),
                   [alpha](float old_val, float new_val) -> float {
                     return (1.0f - alpha) * old_val + alpha * new_val;
                   });
  }

  // Computing probability of each point to be in the interest area.
  // The mean of this distribution should be mean = robot_height or
  // robot_height/2. The standard deviation should be stddev = robot_height or
  // robot_height/2.
  float gaussian_mapping(float value, float mean, float stddev) {
    float exponent = -((value - mean) * (value - mean)) / (2 * stddev * stddev);
    float gaussian_value = std::exp(exponent);
    // return gaussian_value / (stddev * std::sqrt(2 * M_PI)); // normalized
    //  Using unnormalized value for mapping
    return gaussian_value;
  }

  // Method to apply KD-Tree clustering on pointcloud
  pcl::PointCloud<pcl::PointXYZRGB>::Ptr
  cluster_filter(pcl::PointCloud<pcl::PointXYZRGB>::Ptr input_cloud) {
    // Prepare output
    pcl::PointCloud<pcl::PointXYZRGB>::Ptr clustered_cloud(
        new pcl::PointCloud<pcl::PointXYZRGB>);
    if (input_cloud->empty()) {
      return clustered_cloud;
    }

    // Build a KD-Tree for nearest-neighbor search
    tree->setInputCloud(input_cloud);

    // Vector of cluster indices (each cluster is a
    // vector<int> of point indices)
    std::vector<pcl::PointIndices> cluster_indices;

    // Configure clustering
    pcl::EuclideanClusterExtraction<pcl::PointXYZRGB> ec;
    ec.setClusterTolerance(
        grid_map.filter.cluster_tolerance); // Max distance between
                                            // points in a cluster
                                            // [m]
    ec.setMinClusterSize(
        grid_map.filter.cluster_min_size); // Min points per cluster
    ec.setMaxClusterSize(
        grid_map.filter.cluster_max_size); // Max points per cluster
    ec.setSearchMethod(tree);
    ec.setInputCloud(input_cloud);
    ec.extract(cluster_indices);

    // Extract clusters that meet your criteria
    pcl::ExtractIndices<pcl::PointXYZRGB> extract;
    extract.setInputCloud(input_cloud);

    for (const auto &indices : cluster_indices) {
      if (indices.indices.size() < grid_map.filter.cluster_min_size)
        continue;

      pcl::PointIndices::Ptr cluster_ptr(new pcl::PointIndices(indices));
      pcl::PointCloud<pcl::PointXYZRGB>::Ptr cluster_cloud(
          new pcl::PointCloud<pcl::PointXYZRGB>);

      extract.setIndices(cluster_ptr);
      extract.setNegative(false);
      extract.filter(*cluster_cloud);

      *clustered_cloud += *cluster_cloud;
    }

    return clustered_cloud;
  }

  // Method that applies multiple filtering layers on the 3D pointcloud.
  pcl::PointCloud<pcl::PointXYZRGB>::Ptr
  filter_cloud(pcl::PointCloud<pcl::PointXYZRGB>::Ptr raw_cloud) {

    if (!grid_map.filter.filter_enable) {
      return raw_cloud;
    }

    pcl::PointCloud<pcl::PointXYZRGB>::Ptr cloud_filtered(
        new pcl::PointCloud<pcl::PointXYZRGB>);
    pcl::PointCloud<pcl::PointXYZRGB>::Ptr cloud_clustered(
        new pcl::PointCloud<pcl::PointXYZRGB>);

    if (raw_cloud->empty()) {
      return cloud_filtered;
    }
    // RCLCPP_INFO(this->get_logger(), "raw_cloud size: %zu",
    // raw_cloud->size());

    // Radius Outlier Removal (first) — remove isolated noise clusters
    if (grid_map.filter.ror_enable) {
      ror.setInputCloud(raw_cloud);
      ror.setRadiusSearch(grid_map.filter.ror_radius); // slightly larger radius
      ror.setMinNeighborsInRadius(grid_map.filter.ror_min_neighbors_in_radius);
      ror.filter(*cloud_filtered);
    }

    // RCLCPP_INFO(this->get_logger(), "after ROR size: %zu",
    // cloud_filtered->size());
    //  Statistical Outlier Removal (refine locally)
    if (grid_map.filter.sor_enable) {
      sor.setInputCloud(cloud_filtered);
      sor.setMeanK(grid_map.filter.sor_mean);
      sor.setStddevMulThresh(
          grid_map.filter
              .sor_stddev_mul_thresh); // loosen this if too many points vanish
      sor.filter(*cloud_filtered);
    }

    // RCLCPP_INFO(this->get_logger(), "after SOR size: %zu",
    // cloud_filtered->size());
    //  PassThrough filter (z-band filtering)
    if (grid_map.filter.pass_enable) {
      pass.setInputCloud(cloud_filtered);
      pass.setFilterFieldName("z");
      pass.setFilterLimits(
          grid_map.filter.pass_z_min,
          grid_map.filter.pass_z_max); // only keep 0–2m height range
      pass.filter(*cloud_filtered);
    }

    // RCLCPP_INFO(this->get_logger(), "after PassThrough size: %zu",
    // cloud_filtered->size());
    //  VoxelGrid (smooth/compact)
    if (grid_map.filter.voxel_enable) {
      voxel.setInputCloud(cloud_filtered);
      voxel.setLeafSize(grid_map.filter.voxel_lx, grid_map.filter.voxel_ly,
                        grid_map.filter.voxel_lz);
      voxel.filter(*cloud_filtered);
    }

    // RCLCPP_INFO(this->get_logger(), "after VoxelGrid size: %zu",
    // cloud_filtered->size());
    if (grid_map.filter.cluster_enable) {
      cloud_clustered = cluster_filter(cloud_filtered);
      // RCLCPP_INFO(this->get_logger(), "after Clustering size: %zu",
      // cloud_clustered->size());
      return cloud_clustered;
    }

    return cloud_filtered;
  }

  void occupancy_grid_callback(
      const sensor_msgs::msg::PointCloud2::ConstSharedPtr input_msg) {
    pcl::PointCloud<pcl::PointXYZRGB>::Ptr out_cloud(
        new pcl::PointCloud<pcl::PointXYZRGB>);
    pcl::fromROSMsg(*input_msg, *out_cloud);
    // Initialize grid
    grid_map.initGrid(intensity_grid);
    grid_map.initGrid(height_grid);
    grid_map.initGridMap(intensity_gridmap, "intensity");
    grid_map.initGridMap(height_gridmap, "height");

    std::vector<signed char> hpoints(grid_map.cell_num_x * grid_map.cell_num_y);
    std::vector<float> ipoints(grid_map.cell_num_x * grid_map.cell_num_y, 0.0);
    float gaussian_z_probability = 1.0f;
    // initialize grid vectors: -128 & 0
    for (auto &p : hpoints) {
      p = -128.0;
    }
    for (auto &p : ipoints) {
      p = 0.0;
    }
    // Filtering the point cloud prior to 2D grid map construction
    out_cloud = filter_cloud(out_cloud);
    // Starting to build occupancy grid
    constexpr float kOriginDeadzone = 0.01f;
    for (const auto &p : out_cloud->points) {
      if (std::isnan(p.x) || std::isnan(p.y) || std::isnan(p.z)) {
        continue;
      }
      if (p.z < grid_map.filter.z_min || p.z > grid_map.filter.z_max) {
        continue;
      }
      if (std::abs(p.x) <= kOriginDeadzone) {
        continue;
      }
      if (p.x <= grid_map.bottomright_x || p.x >= grid_map.topleft_x ||
          p.y <= grid_map.bottomright_y || p.y >= grid_map.topleft_y) {
        continue;
      }

      PointXY cell = grid_map.getIndex(p.x, p.y);
      if (cell.x >= grid_map.cell_num_x || cell.y >= grid_map.cell_num_y) {
        RCLCPP_WARN_STREAM(this->get_logger(),
                           "Cell out of range: "
                               << cell.x << " - " << grid_map.cell_num_x
                               << " ||| " << cell.y << " - "
                               << grid_map.cell_num_y);
        continue;
      }

      // Converting RGB value to intensity
      uint32_t rgb_uint;
      std::memcpy(&rgb_uint, &p.rgb, sizeof(uint32_t));
      uint8_t r = (rgb_uint >> 16) & 0x0000ff;
      uint8_t g = (rgb_uint >> 8) & 0x0000ff;
      uint8_t b = (rgb_uint) & 0x0000ff;
      float intensity = (r + g + b) / 3.0f;

      gaussian_z_probability =
          grid_map.filter.gaussian_enable
              ? gaussian_mapping(p.z, grid_map.filter.gaussian_mean,
                                 grid_map.filter.gaussian_stddev)
              : 1.0f;

      size_t idx = cell.y * grid_map.cell_num_x + cell.x;
      ipoints[idx] += intensity * grid_map.intensity_factor * gaussian_z_probability;
      hpoints[idx] = p.z * grid_map.height_factor;
    }

    // Averaging grid maps if either of averaging methods is enabled
    if (grid_map.filter.normal_averaging_enable &&
        grid_map.filter.moving_average_enable) {
      RCLCPP_WARN_STREAM_ONCE(this->get_logger(),
                              "Both normal and moving average are enabled. "
                              "Only normal averaging will be applied.");
    }

    // Remapping values between [0, 100] to be compliant with NAV2 occupancy
    // grid.
    std::vector<signed char> display_ipoints(ipoints.size());
    if ((grid_map.filter.normal_averaging_enable ||
         grid_map.filter.moving_average_enable) == false) {
      for (size_t i = 0; i < ipoints.size(); ++i) {
        display_ipoints[i] = static_cast<signed char>(
            std::clamp(static_cast<int>(ipoints[i]), 0, 100));
      }
    } else if (grid_map.filter.normal_averaging_enable) {
      update_normal_average(ipoints, normal_avg_count);
      for (size_t i = 0; i < ipoints.size(); ++i) {
        display_ipoints[i] = static_cast<signed char>(
            std::clamp(static_cast<int>(avg_ipoints[i]), 0, 100));
      }
    } else if (grid_map.filter.moving_average_enable) {
      update_moving_average(ipoints, grid_map.filter.ma_alpha);
      for (size_t i = 0; i < ipoints.size(); ++i) {
        display_ipoints[i] = static_cast<signed char>(
            std::clamp(static_cast<int>(avg_ipoints[i]), 0, 100));
      }
    }

    intensity_grid->header.stamp = this->now();
    intensity_grid->header.frame_id = input_msg->header.frame_id;
    intensity_grid->info.map_load_time = this->now();
    intensity_grid->data = display_ipoints;
    height_grid->header.stamp = this->now();
    height_grid->header.frame_id = input_msg->header.frame_id;
    height_grid->info.map_load_time = this->now();
    height_grid->data = hpoints;

    // Convert to GridMap format
    intensity_gridmap->header.stamp = this->now();
    intensity_gridmap->header.frame_id = input_msg->header.frame_id;
    for (size_t i = 0; i < ipoints.size(); ++i) {
      intensity_gridmap->data[0].data[i] =
          static_cast<float>(display_ipoints[i]) / 127.0f; // Normalize to float
    }

    height_gridmap->header.stamp = this->now();
    height_gridmap->header.frame_id = input_msg->header.frame_id;
    for (size_t i = 0; i < hpoints.size(); ++i) {
      height_gridmap->data[0].data[i] =
          static_cast<float>(hpoints[i]) / 127.0f; // Normalize to float
    }

    pub_hgrid->publish(*height_grid);
    pub_igrid->publish(*intensity_grid);
    pub_hgridmap->publish(*height_gridmap);
    pub_igridmap->publish(*intensity_gridmap);
    // pub_hgrid->publish(height_grid);
    if (verbose1) {
      RCLCPP_INFO_STREAM(this->get_logger(),
                         "Published " << grid_map.mapi_topic_name.c_str()
                                      << " and "
                                      << grid_map.maph_topic_name.c_str());
    }
  }

  // Declaring gridmap average vector
  float normal_avg_count = 0;
  std::vector<float> avg_ipoints;

  // Declaring filters
  pcl::search::KdTree<pcl::PointXYZRGB>::Ptr tree =
      pcl::search::KdTree<pcl::PointXYZRGB>::Ptr(
          new pcl::search::KdTree<pcl::PointXYZRGB>());
  pcl::RadiusOutlierRemoval<pcl::PointXYZRGB> ror;
  pcl::StatisticalOutlierRemoval<pcl::PointXYZRGB> sor;
  pcl::PassThrough<pcl::PointXYZRGB> pass;
  pcl::VoxelGrid<pcl::PointXYZRGB> voxel;

  rclcpp::Publisher<nav_msgs::msg::OccupancyGrid>::SharedPtr pub_igrid,
      pub_hgrid;
  rclcpp::Publisher<grid_map_msgs::msg::GridMap>::SharedPtr pub_igridmap,
      pub_hgridmap;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_pc2_;
  OnSetParametersCallbackHandle::SharedPtr callback_handle_;
  std::string cloud_in_topic = "nonground";
  bool verbose1 = true, verbose2 = false;
  GridMap grid_map;
  size_t count_;

  // Grid message storage
  std::shared_ptr<nav_msgs::msg::OccupancyGrid> height_grid =
      std::make_shared<nav_msgs::msg::OccupancyGrid>();
  std::shared_ptr<nav_msgs::msg::OccupancyGrid> intensity_grid =
      std::make_shared<nav_msgs::msg::OccupancyGrid>();
  std::shared_ptr<grid_map_msgs::msg::GridMap> height_gridmap =
      std::make_shared<grid_map_msgs::msg::GridMap>();
  std::shared_ptr<grid_map_msgs::msg::GridMap> intensity_gridmap =
      std::make_shared<grid_map_msgs::msg::GridMap>();
};
int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PointCloudToGrid>());
  rclcpp::shutdown();
  return 0;
}