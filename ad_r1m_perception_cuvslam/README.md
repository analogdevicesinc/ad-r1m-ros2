
# `ad_r1m_perception_cuvslam` ROS2 Package

This package provides the launch files and URDF descriptions needed to start and use the base navigation functionality of the AD_R1M platform together with NVIDIA® Isaac™ ROS Visual SLAM.  
Note: This is a *high‑level overview*. Full setup instructions and detailed documentation are available on the [official AD-R1M documentation page](https://developer.analog.com/docs/system-level/solutions/reference-designs/ad-r1m/index.html#getting-started).

## Prerequisites

### Hardware
- AD_R1M mobile robot platform
- NVIDIA® Jetson™ AGX Orin or any desktop station with an NVIDIA GPU  
  (setup instructions are provided only for the AGX Orin variant)
- Intel® RealSense™ camera(s)  
  (ZED cameras are also supported by NVIDIA Isaac ROS, but they are not part of our standard hardware setup. For ZED configuration details, see: https://nvidia-isaac-ros.github.io/getting_started/sensors/zed_setup.html)

### Software
- Intel RealSense drivers and ROS2 packages
- Isaac ROS Visual SLAM packages installed on your NVIDIA platform

### Simulation
- Gazebo Ignition  
  A Gazebo model of AD‑R1M equipped with a Intel RealSense D435i is provided for testing AD‑R1M + Isaac ROS Visual SLAM functionality in simulation.

All setup steps and requirements related to AD‑R1M and NVIDIA Isaac ROS Visual SLAM can be found on the official documentation page.

## Use Cases

### 1) Real Robot

After completing all setup steps from the official documentation:

- Calibrate the extrinsic parameters of your RealSense camera (depending on how it is mounted on the robot) using the file:  
  **urdf/single_realsense_calibration.urdf**

  Despite the file name, you may configure multiple RealSense cameras as long as you provide the appropriate static transforms.

```r
    <robot name="adrd_demo_ros2">
      <link name="ad_r1m_0/base_link" />

      <joint name="camera1" type="fixed">
        <parent link="ad_r1m_0/base_link"/>
        <child link="camera1_link"/>
        <origin xyz="0.335 0.0 0.0" rpy="0 0 0"/>
      </joint>
      ...
    </robot>
```

  The default values correspond to a camera mounted in front of the robot, above the ToF camera (0.335 m translation on the X-axis and zero rotation on all axes).

- On your NVIDIA® Jetson™ AGX Orin, run the Isaac ROS Docker container:

```r
    cd $ISAAC_ROS_WS/src/isaac_ros_common
    ./scripts/run_dev.sh -i ros2_humble.realsense.visualslam
```

- Inside the container:

```r
    source install/setup.sh
    ros2 launch ad_r1m_perception_cuvslam cuvslam_multirealsense.launch.py
```

This starts all required RealSense and Isaac ROS Visual SLAM nodes.

### 2) Simulation

- Connect the host computer (running Gazebo) to the AGX Orin via Ethernet.

- Launch the simulation on the host:

```r
    ros2 launch ad_r1m_perception_cuvslam robot_realsense_sim.launch.py \
        local_models_path:=<path_to_your_models> \
        world_name:=<your_world_name.world>
```

- On the NVIDIA Jetson AGX Orin, run the Docker container:

```r
    cd $ISAAC_ROS_WS/src/isaac_ros_common
    ./scripts/run_dev.sh -i ros2_humble.realsense.visualslam
```

- Inside the container:

```r
    source install/setup.sh
    ros2 launch ad_r1m_perception_cuvslam vslam_single_realsense.launch.py
```

## Configuration
Configuration files for RealSense cameras and Isaac ROS Visual SLAM parameters can be found in **config/**. 
- The setup using the real robot loads: *vslam_single_realsense.yaml*
- The simulation setup uses: *cuvslam_single_realsense.yaml*

More details on how to configure Isaac ROS Visual SLAM or RealSense parameters can be found at their official documentation pages:
- https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_visual_slam/isaac_ros_visual_slam/index.html
- https://github.com/realsenseai/realsense-ros