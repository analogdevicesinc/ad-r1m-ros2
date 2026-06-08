7) AD-R1M and cuVSLAM setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Up to this point, the NVIDIA Docker container has been configured with all required dependencies for running cuVSLAM with a RealSense camera. To enable full integration of cuVSLAM on the AD-R1M platform, a few additional configuration steps are necessary.

The following steps should be run on the AGX Orin platform. Open a new terminal and run the following commands:

.. code-block:: bash
    
    cd $ISAAC_ROS_WS
    git clone https://github.com/analogdevicesinc/ad-r1m-ros2
    cp -r ad-r1m-ros2/ad_r1m_perception_cuvslam/* src/isaac-ros-common/docker

This step copies the additional Dockerfiles and entrypoint scripts required to install extra dependencies inside 
the container and to enable proper communication between the NVIDIA Docker environment and the AD-R1M platform.

These changes ensure that the container can successfully run zenoh using mDNS, which is necessary for discovering 
and communicating with the robot (ad-r1m-0) over Ethernet.

Go to the scripts folder in the **isaac-ros-common** package:

.. code-block:: bash

    cd /src/isaac_ros_common/scripts

Modify the **run_dev.sh** script from **$ISAAC_ROS_WS/src/isaac_ros_common** as follows:
    * Look for the following lines of code 

    .. code-block:: bash

        BASE_NAME="isaac_ros_dev-$PLATFORM"
        if [[ ! -z "$CONFIG_CONTAINER_NAME_SUFFIX" ]] ; then
            BASE_NAME="$BASE_NAME-$CONFIG_CONTAINER_NAME_SUFFIX"
        fi
        CONTAINER_NAME="$BASE_NAME-container"

        # Remove any exited containers.
        if [ "$(docker ps -a --quiet --filter status=exited --filter name=$CONTAINER_NAME)" ]; then
            docker rm $CONTAINER_NAME > /dev/null
        fi
    
    * Insert the following lines after BASE_NAME="isaac_ros_dev-$PLATFORM". This ensures that intermediate images are not left unnamed and that each image is tagged based on the Dockerfiles used in the build process:

    .. code-block:: bash

        if [[ ! -z "$IMAGE_KEY" && "$IMAGE_KEY" != "ros2_humble" ]]; then
        IMAGE_KEY_SAFE="${IMAGE_KEY//./-}"   # replace dots with dashes
        BASE_NAME="${BASE_NAME}-${IMAGE_KEY_SAFE}"
        fi
    
    * In order to automatically configure Zenoh at startup, set the necessary Docker container environment variables:

    .. code-block:: bash

        docker run -it --rm \
            -e ROS_NAMESPACE=ad_r1m_0 \
            -e RMW_IMPLEMENTATION=rmw_zenoh_cpp \
            -e ROBOT_TCP_NAME=ad-r1m-0 \
            -e ZENOH_CONFIG_OVERRIDE="connect/endpoints=[\"tcp/ad-r1m-0.local:7447\"];mode=\"client\"" \
            --privileged \
            --network host \
            --ipc=host \
            "${DOCKER_ARGS[@]}" \
            -v "$ISAAC_ROS_DEV_DIR":/workspaces/isaac_ros-dev \
            -v /etc/localtime:/etc/localtime:ro \
            --name "$CONTAINER_NAME" \
            --runtime nvidia \
            --entrypoint /usr/local/bin/scripts/workspace-entrypoint.sh \
            --workdir /workspaces/isaac_ros-dev \
            "$BASE_NAME" \
            /bin/bash

After completing all these steps, you can build the updated Docker image by running:

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/isaac_ros_common
    ./scripts/run_dev.sh -i ros2_humble.realsense.visualslam

This command creates a new image layer on top of the base Docker image provided by NVIDIA, incorporating all 
additional dependencies and configuration changes.

You can then launch a new container instance from this updated image using the same script: 

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/isaac_ros_common
    ./scripts/run_dev.sh -i ros2_humble.realsense.visualslam
