# AD-R1M example apps

A collection of example apps that build on top of the AD-R1M software stack:

* `waypoint_app.py`: Send target coordinates to the nav2 stack running on the robot.
* `addon_lift.py`: Send GPIO commands to an external hardware module in response to ROS 2 messages.

## Build and runtime environment

We provide two options for running these examples in a proper ROS 2 environment:

1. Use a [Pixi](https://pixi.prefix.dev/) workspace -- very easy to set up, but is experimental and has its limits (e.g. not all ROS packages available)
1. Build and run a Docker container -- relatively complex, but you have almost complete control of the runtime environment.

### Build and run in a Pixi environment

First, install Pixi using the official [installation steps](https://pixi.prefix.dev/latest/installation/).

Enter this directory and perpare the Pixi environment by installing all dependencies. This includes ROS 2 packages, pypi packages, etc.

```
cd .../ad_r1m_ros2/ad_r1m_examples/
pixi install
```

When inside this directory, you can run ROS 2 commands by prefixing them with `pixi run`:

```
pixi run ros2 run ad_r1m_examples waypoint_follower.py
```

... or by entering a `pixi shell` environment:

```
pixi shell
ros2 run ad_r1m_examples waypoint_follower.py
```

When using `pixi run`, the package will be automatically rebuilt if its contents change (controlled by the `package.build.config.extra-input-globs` option in `pixi.toml`).

### Build and run in a Docker container

The `Dockerfile` inside this folder builds the `ad_r1m_examples` package inside a ROS 2 container. Run the build with:

```
docker buildx build . -t ad_r1m_examples
```

After a successful build, you may run example code like so:

```
docker run -it --network=host --ipc=host --pid=host \
    ad_r1m_examples ros2 run ad_r1m_examples waypoint_follower.py \
    --ros-args -r __ns:=/ad_r1m_123
```

Explanation of the arguments:

* `-it` enable interactive tty
* `--network=host --ipc=host --pid=host` required to make cross-container DDS communication work
* `ad_r1m_examples` - name of the image, should match `-t ...` argument from the build step
* `ros 2 run ...` - ROS 2 command to run inside the container

Alternatively, you may also just start a bash shell inside the container and run commands there:

```
docker run -it --network=host --ipc=host --pid=host ad_r1m_examples
```

## Example: Waypoint follower

Open `scripts/waypoint_follower.py` and take a look around.

For this exercise, you must edit the following section:

```
    # ____________________ CHANGE THIS ____________________
    waypoints = [
        Waypoint(x = -0.9 , y = -0.5 , heading = 90.0 ),
        Waypoint(x = -0.9 , y = +0.5 , heading = 0.0 ),
        Waypoint(x =  0.0 , y = -0.5 , heading = 300.0 ),
        Waypoint(x = +0.9 , y = +0.5 , heading = 270.0 ),
        Waypoint(x = +0.9 , y = -0.2 , heading = 180.0  ),
    ]
    # ^^^^^^^^^^^^^^^^^^^^ CHANGE THIS ^^^^^^^^^^^^^^^^^^^^
```

This is a list of waypoints to be followed in order. Each specifies
x, y coordinates (in meters) and a heading (in degrees). The default
list traces an "M" shaped path.

**Create your own waypoint list!** Change the coordinates, add more waypoints, delete some, etc.

Follow the instructions above to build the package into a Docker image (run the `docker buildx build` command), then run this example with:

```
# Prefix this command with `docker run ...` or `pixi run`:
ros2 run ad_r1m_examples waypoint_follower.py
```

If using a robot namespace (e.g. `ad_r1m_123`), add the following remap rule:

```
# Prefix this command with `docker run ...` or `pixi run`:
ros2 run ad_r1m_examples waypoint_follower.py --ros-args -r __ns:=/ad_r1m_123
```

## Example: Hardware add-on

TODO :^)

