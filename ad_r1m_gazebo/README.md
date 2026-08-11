# AD-R1M Gazebo Simulation

Gazebo Classic simulation package for the AD-R1M robot.

## Quick Start

```bash
# Build the workspace (downloads models automatically)
colcon build --packages-select ad_r1m_gazebo
source install/setup.bash

# Launch simulation with default empty world
ros2 launch ad_r1m_gazebo launch_sim.launch.py
```

## Model Setup

Third-party models are downloaded automatically during `colcon build` via CMake ExternalProject.

**Sources:**
- [OSRF Gazebo Models](https://github.com/osrf/gazebo_models) (CC BY 3.0)
- [OSRF ARIAC](https://bitbucket.org/osrf/ariac) (Apache 2.0)
- [OSRF ServiceSim](https://github.com/osrf/servicesim) (Apache 2.0)

To skip downloading models (CI or offline builds):
```bash
colcon build --packages-select ad_r1m_gazebo --cmake-args -DDOWNLOAD_GAZEBO_MODELS=OFF
```

To re-download models, clean and rebuild:
```bash
colcon build --packages-select ad_r1m_gazebo --cmake-clean-cache
```

## Available Worlds

| World | Description | Robot Spawn |
|-------|-------------|-------------|
| `empty.world` | Empty world (default) | (0, 0, 0) |
| `obstacles.world` | Simple obstacles for testing | (0, 0, 0) |
| `factory.world` | Industrial factory environment | (10, -2.5, 0) |
| `aws_office.world` | AWS office environment | (-5, 3, 0.05) |

Robot spawn positions are configured in `config/worlds.yaml`.

### Running Different Worlds

```bash
# Factory world
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world

# AWS Office world
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/aws_office.world

# Spawn positions are configured per-world in config/worlds.yaml
```

## Localization

### Using AMCL (recommended for navigation)

Use AMCL localization with a pre-built map. The factory map was built with the robot starting at odom origin (0, 0), so initial pose should be (0, 0):

```bash
# Terminal 1: Start simulation
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world

# Terminal 2: Start AMCL localization (initial pose at map origin)
ros2 launch ad_r1m_navigation localization_launch.py \
  use_sim_time:=true \
  map:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/maps/factory_map.yaml \
  initial_pose_x:=0.0 \
  initial_pose_y:=0.0
```

Note: The map is built in the odom frame, so the initial pose is relative to where the robot spawned, not the world origin.

### AWS Office Localization

```bash
# Terminal 1: Start simulation with AWS office world
ros2 launch ad_r1m_gazebo launch_sim.launch.py world:=aws_office.world

# Terminal 2: Start AMCL localization
ros2 launch ad_r1m_navigation localization_launch.py \
  use_sim_time:=true \
  map:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/maps/aws_office.yaml \
  initial_pose_x:=0.0 \
  initial_pose_y:=0.0
```

## Navigation (Factory World)

Run autonomous navigation with Nav2 using the pre-built factory map:

```bash
# Terminal 1: Start simulation
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world

# Terminal 2: Start AMCL localization
ros2 launch ad_r1m_navigation localization_launch.py \
  use_sim_time:=true \
  map:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/maps/factory_map.yaml \
  initial_pose_x:=0.0 \
  initial_pose_y:=0.0
```

**Note:** After launching localization, change RViz Global Options Fixed Frame from `odom` to `map`.

```bash
# Terminal 3: Start Nav2 navigation
ros2 launch ad_r1m_navigation navigation_launch.py \
  use_sim_time:=true \
  params_file:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/config/nav2_params_sim_worlds.yaml
```

Use "2D Goal Pose" in RViz to send navigation goals.

## Navigation (AWS Office World)

Run autonomous navigation with Nav2 using the AWS office map:

```bash
# Terminal 1: Start simulation
ros2 launch ad_r1m_gazebo launch_sim.launch.py world:=aws_office.world

# Terminal 2: Start AMCL localization
ros2 launch ad_r1m_navigation localization_launch.py \
  use_sim_time:=true \
  map:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/maps/aws_office.yaml \
  initial_pose_x:=0.0 \
  initial_pose_y:=0.0
```

**Note:** After launching localization, change RViz Global Options Fixed Frame from `odom` to `map`.

```bash
# Terminal 3: Start Nav2 navigation
ros2 launch ad_r1m_navigation navigation_launch.py \
  use_sim_time:=true \
  params_file:=$(ros2 pkg prefix ad_r1m_navigation)/share/ad_r1m_navigation/config/nav2_params_sim_worlds.yaml
```

Use "2D Goal Pose" in RViz to send navigation goals.

## Launch Arguments

### launch_sim.launch.py

| Argument | Default | Description |
|----------|---------|-------------|
| `world` | `empty.world` | Path to world file |
| `namespace` | `""` | Robot namespace for multi-robot |

Spawn position (x, y, z) and orientation (R, P, Y) are configured per-world in `config/worlds.yaml`.

## Troubleshooting

### Models not visible in Gazebo
1. Rebuild to re-download models: `colcon build --packages-select ad_r1m_gazebo --cmake-clean-cache`
2. The launch file automatically sets `GAZEBO_MODEL_PATH`. If models still don't appear, manually set:
```bash
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/models
```

### TF_OLD_DATA errors
Kill all processes and restart fresh:
```bash
pkill -9 -f gazebo; pkill -9 -f ros
```

### Map not appearing in RViz
- Ensure fixed frame is set to `map`
- Add a Map display subscribed to `/map` topic
- Wait for RTAB-Map to initialize (first scan)
