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

Install these before running:

```bash
sudo apt install \
    ros-humble-imu-filter-madgwick \
    ros-humble-robot-localization \
    ros-humble-twist-mux \
    ros-humble-gazebo-ros \
    ros-humble-gazebo-ros2-control \
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
