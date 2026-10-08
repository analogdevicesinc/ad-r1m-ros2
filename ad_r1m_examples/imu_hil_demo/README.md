# IMU Hardware-in-the-Loop Demo

Control the AD-R1M robot's yaw in Gazebo simulation using a real IMU sensor.

A P-controller reads orientation from a physical IMU (via the Madgwick filter)
and sends angular velocity commands so the simulated robot tracks the real
sensor's yaw. Forward/backward motion is controlled via keyboard (W/S keys).

## Data flow

```
Real IMU --/imu/data_raw--> Madgwick --/imu/data--> HIL Controller --cmd_vel_hil--> twist_mux --> diff_drive
                                                         ^
                                              sim odom --'  (yaw feedback)
```

## Dependencies

Install these before running (requires the OSRF Gazebo apt repository for
Harmonic packages):

```bash
sudo apt install \
    ros-humble-ros-gz \
    ros-humble-gz-ros2-control \
    ros-humble-imu-filter-madgwick \
    ros-humble-robot-localization \
    ros-humble-twist-mux \
    ros-humble-controller-manager \
    ros-humble-diff-drive-controller \
    ros-humble-joint-state-broadcaster \
    ros-humble-robot-state-publisher \
    ros-humble-tf-transformations \
    ros-humble-rviz2 \
    ros-humble-xacro
```

## Build

From the workspace root:

```bash
colcon build --packages-select ad_r1m_examples
source install/setup.bash
```

## Run

```bash
ros2 launch ad_r1m_examples imu_hil_demo/launch/hil_demo.launch.py
```

To launch without RViz:

```bash
ros2 launch ad_r1m_examples imu_hil_demo/launch/hil_demo.launch.py use_rviz:=false
```

## Configuration

All parameters are in `config/`:

| File               | Description                                      |
|--------------------|--------------------------------------------------|
| hil_params.yaml    | IMU/odom topics, P-gain, speed, control rate     |
| madgwick.yaml      | Madgwick filter settings (gain, frequency, etc.) |
| hil_ekf.yaml       | EKF fusion config (wheel odom + sim IMU)         |
| twist_mux_hil.yaml | twist_mux channels and priorities                |

## Controls

| Key   | Action            |
|-------|-------------------|
| W     | Nudge forward     |
| S     | Nudge backward    |
| SPACE | Stop              |
| Q     | Quit              |

Yaw is controlled automatically by the real IMU (no keyboard input needed for turning).

## Docker

Build from the `imu_hil_demo/` directory:

```bash
cd <path-to>/ad-r1m-ros2/ad_r1m_examples/imu_hil_demo
docker build -t ad_r1m_hil_demo .
```

Allow X11 access from the container:

```bash
xhost +local:docker
```

Run with GUI support, host networking (for ROS topic access), and the
repository mounted as a volume:

```bash
docker run -it --rm \
    --net=host \
    --ipc=host \
    -e DISPLAY=$DISPLAY \
    -e XAUTHORITY=$XAUTHORITY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $XAUTHORITY:$XAUTHORITY:ro \
    -v <path-to>/ad-r1m-ros2:/ros2_ws/src/ad-r1m-ros2 \
    ad_r1m_hil_demo
```

Inside the container, build and launch:

```bash
colcon build --packages-select ad_r1m_description ad_r1m_control ad_r1m_gazebo ad_r1m_examples
source install/setup.bash
ros2 launch ad_r1m_examples hil_demo.launch.py
```
