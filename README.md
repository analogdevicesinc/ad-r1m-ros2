# AD-R1M Software

The AD-R1M robot platform runs on ROS 2. This repository is home to a number of ROS 2 packages, as well as CI, platform-specific setup scripts, and other miscellaneous small bits of adjacent software.

<img align="right" src="ad_r1m/doc/figures/ad-r1m.png" alt="3D render of AD-R1M: a white box with a camera up front, and a side panel with buttons and indicator lights" style="width: 20em" />

## ROS 2 packages

Most top-level folders are ROS 2 packages:

* `ad_r1m` -- Documentation package
* `ad_r1m_robot` -- Metapackage for AD-R1M real robot
* `ad_r1m_sim` -- Metapackage for AD-R1M simulated robot

* `ad_r1m_description` -- AD-R1M description (URDF, meshes, etc.)
* `ad_r1m_control` -- AD-R1M control loop: ros2_control stack, state estimation
* `ad_r1m_gazebo` -- AD-R1M simulated robot in Gazebo Classic
* `ad_r1m_bringup` -- AD-R1M real robot bringup
* `ad_r1m_navigation` -- AD-R1M default navigation stack
* `ad_r1m_perception_aditof` -- AD-R1M default perception stack using an EVAL-ADTF3175D-NXZ
* `ad_r1m_perception_cuvslam` -- AD-R1M perception using Nvidia cuVSLAM
* `ad_r1m_pointcloud_to_occupancygrid` -- Convert PointCloud2 to OccupancyGrid for integrating cuVSLAM output with nav2
* `ad_r1m_examples` -- Example apps that build on top of the AD-R1M stack

## Docker containers

We build the ROS 2 packages in Docker images and use them as the preferred method of distribution. This provides a known-working environment that can be effortlessly deployed to robots both on the bench as well as in action.

| Docker tag | Built packages | ROS distro | CI |
|------------|----------------|------------|----|
| `ad-r1m:sim` <br/> `ad-r1m:sim-humble` | `ad_r1m_sim` | Humble | TODO |
| `ad-r1m:robot` <br/> `ad-r1m:robot-humble` | `ad_r1m_robot` | Humble | TODO |
| `ad-r1m:robot-jazzy` | `ad_r1m_robot` | Jazzy | TODO |

Relevant folders:

* `docker`

## Hardware variant support

The AD-R1M supports a number of hardware variants, yet still, the ROS 2 docker containers should be kept agnostic to these. To accomplish this, we build packages that handle platform-specific system-level bootstrapping: systemd units and overrides, udev rules, extra packages, utility scripts, etc., and provide the Docker containers with a common interface (e.g., by mapping the right host tty to the remote control tty in the container).

These are Debian packages, making system bootstrapping a matter of running something like `apt install ad-r1m-system-rpi5`. This has the added benefit of decoupling robot bootstrapping from the base image, enabling users to customize their robot's OS image, as opposed to being tied to one specific hand-crafted "grandma's secret recipe" image.

| Hardware variant | Components | Packaging method | CI |
|------------------|------------|------------------|----|
| AD-R1M (default) | <ul><li>Raspberry Pi 5 running ADI Kuiper Linux</li><li>ADRD4161-01Z carrier</li><li>ADRD3161-01Z motor drives</li><li>ADRD5161-01Z BMS</li></ul> | Debian package: `ad-r1m-system-rpi5` | TODO |

This does not include packages for the supported coprocessing platforms, such as the Nvidia Jetson platforms, because they currently don't run robot control directly, but rather only act on the behaviour / processing level.

Relevant folders:

* `system` -- System-level bootstrapping content
    * `common`
    * `rpi5`
    * `adrd3161`
    * ...
* `packaging` -- Packaging logic

## Documentation

Comprehensive documentation for the AD-R1M robot platform is available at:

**https://analogdevicesinc.github.io/ad-r1m-ros2/**

The documentation includes:
- Quick start guide
- Hardware and software setup
- System architecture
- Usage examples and tutorials
- Advanced topics (NVIDIA AGX Orin integration, cuVSLAM)
- Troubleshooting

### Building Documentation Locally

```bash
cd ad_r1m/doc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
mkdir -p _build && cd _build
rosdoc2 build --package-path ../ad_r1m
```

Generated documentation will be available in `_build/docs_output/ad_r1m/index.html`.

