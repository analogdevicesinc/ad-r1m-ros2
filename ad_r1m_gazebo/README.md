# AD-R1M Gazebo Simulation

Gazebo Classic simulation package for the AD-R1M robot.

## Quick Start

```bash
# Build the workspace
colcon build --packages-select ad_r1m_gazebo
source install/setup.bash

# Launch simulation with default empty world
ros2 launch ad_r1m_gazebo launch_sim.launch.py
```

## Available Worlds

| World | Description | Robot Spawn |
|-------|-------------|-------------|
| `empty.world` | Empty world (default) | (0, 0) |
| `obstacles.world` | Simple obstacles for testing | (0, 0) |
| `factory.world` | Industrial factory environment | (10, -2.5) |
| `aws_office.world` | AWS office environment | (0, 15) |

Robot spawn positions are configured in `config/worlds.yaml`.

### Running Different Worlds

```bash
# Factory world
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world

# AWS Office world
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/aws_office.world

# Override spawn position
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world \
  x:=5.0 y:=0.0
```

## SLAM Mapping

RTAB-Map SLAM is available as an alternative to SLAM Toolbox.

```bash
# Terminal 1: Start simulation
ros2 launch ad_r1m_gazebo launch_sim.launch.py \
  world:=$(ros2 pkg prefix ad_r1m_gazebo)/share/ad_r1m_gazebo/worlds/factory.world

# Terminal 2: Start RTAB-Map SLAM
ros2 launch ad_r1m_gazebo rtabmap_slam.launch.py

# Terminal 3: Drive the robot to build a map
# Use the teleop keyboard that opens automatically, or:
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Saving a Map

```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map --ros-args -p use_sim_time:=true
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
  use_sim_time:=true
```

Use "2D Goal Pose" in RViz to send navigation goals.

## Launch Arguments

### launch_sim.launch.py

| Argument | Default | Description |
|----------|---------|-------------|
| `world` | `empty.world` | Path to world file |
| `namespace` | `""` | Robot namespace for multi-robot |
| `x` | from worlds.yaml | Robot spawn X position |
| `y` | from worlds.yaml | Robot spawn Y position |

### rtabmap_slam.launch.py

| Argument | Default | Description |
|----------|---------|-------------|
| `use_sim_time` | `true` | Use simulation clock |
| `localization` | `false` | Localization mode (use existing map) |
| `namespace` | `""` | Robot namespace |

## Troubleshooting

### Models not visible in Gazebo
The launch file automatically sets `GAZEBO_MODEL_PATH`. If models still don't appear, manually set:
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
