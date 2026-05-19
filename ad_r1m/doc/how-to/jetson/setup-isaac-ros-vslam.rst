4) Setup Isaac ROS Visual SLAM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

4.1) Clone **isaac_ros_common**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: 
    This step is required only if camera is of RealSense type.
    It should not be run for other types of cameras.

.. code-block:: bash

    cd $ISAAC_ROS_WS/src
    git clone -b release-3.2 https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git isaac_ros_common

Configure the container to include RealSense packages.

.. code-block:: bash
    
    cd $ISAAC_ROS_WS/src/isaac_ros_common/scripts
    touch .isaac_ros_common-config
    echo CONFIG_IMAGE_KEY=ros2_humble.realsense > .isaac_ros_common-config

4.2) Download quickstart data from NGC (Nvidia GPU Cloud)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt install curl jq tar

Download the asset from NGC

.. code-block:: bash

    NGC_ORG="nvidia"
    NGC_TEAM="isaac"
    PACKAGE_NAME="isaac_ros_visual_slam"
    NGC_RESOURCE="isaac_ros_visual_slam_assets"
    NGC_FILENAME="quickstart.tar.gz"
    MAJOR_VERSION=3
    MINOR_VERSION=2
    VERSION_REQ_URL="https://catalog.ngc.nvidia.com/api/resources/versions?orgName=$NGC_ORG&teamName=$NGC_TEAM&name=$NGC_RESOURCE&isPublic=true&pageNumber=0&pageSize=100&sortOrder=CREATED_DATE_DESC"
    AVAILABLE_VERSIONS=$(curl -s \
        -H "Accept: application/json" "$VERSION_REQ_URL")
    LATEST_VERSION_ID=$(echo $AVAILABLE_VERSIONS | jq -r "
        .recipeVersions[]
        | .versionId as \$v
        | \$v | select(test(\"^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$\"))
        | split(\".\") | {major: .[0]|tonumber, minor: .[1]|tonumber, patch: .[2]|tonumber}
        | select(.major == $MAJOR_VERSION and .minor <= $MINOR_VERSION)
        | \$v
        " | sort -V | tail -n 1
    )
    if [ -z "$LATEST_VERSION_ID" ]; then
        echo "No corresponding version found for Isaac ROS $MAJOR_VERSION.$MINOR_VERSION"
        echo "Found versions:"
        echo $AVAILABLE_VERSIONS | jq -r '.recipeVersions[].versionId'
    else
        mkdir -p ${ISAAC_ROS_WS}/isaac_ros_assets && \
        FILE_REQ_URL="https://api.ngc.nvidia.com/v2/resources/$NGC_ORG/$NGC_TEAM/$NGC_RESOURCE/\
    versions/$LATEST_VERSION_ID/files/$NGC_FILENAME" && \
        curl -LO --request GET "${FILE_REQ_URL}" && \
        tar -xf ${NGC_FILENAME} -C ${ISAAC_ROS_WS}/isaac_ros_assets && \
        rm ${NGC_FILENAME}
    fi

4.3) Build **isaac_ros_visual_slam**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Check the CDI (Container Device Interface)**

List the content of CDI:

.. code-block:: bash

    sudo nvidia-ctk cdi list

.. important::
    If the output looks like:

    .. code-block:: bash
        
        INFO[0000] Found 2 CDI devices
        nvidia.com/gpu=0
        nvidia.com/gpu=all
    
    **OR**

    .. code-block:: bash
  
        INFO[0000] Found 4 CDI devices
        nvidia.com/gpu=0
        nvidia.com/gpu=all
        nvidia.com/pva=0
        nvidia.com/pva=all  
    
    you can skip the instructions from the warning displayed bellow and jump at the adding user to docker group step.

.. warning::
    Proceed with the rest of the steps from this warning only if the output looks like the following, particularly if there is no gpu listed besides pva (Programmable Vision Accelerator).

    .. code-block:: bash
 
        INFO[0000] Found 2 CDI devices
        nvidia.com/pva=0
        nvidia.com/pva=all
    
    Generate the CDI spec:

    .. code-block:: bash

        sudo nvidia-ctk cdi generate --mode=csv --output=/etc/cdi/nvidia.yaml

    Install the pva-allow-2 package:

    .. code-block:: bash

        sudo apt update
        sudo apt install software-properties-common
        sudo apt-key adv --fetch-key https://repo.download.nvidia.com/jetson/jetson-ota-public.asc
        sudo add-apt-repository 'deb https://repo.download.nvidia.com/jetson/common r36.4 main'
        sudo apt update
        sudo apt install pva-allow-2

**Add current user to docker group**

.. code-block:: bash

    sudo usermod -aG docker $USER && newgrp docker

**Launch and create the docker container using the run_dev.sh script**

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/isaac_ros_common
    ./scripts/run_dev.sh -d $ISAAC_ROS_WS

.. note::
    Depending on the network speed, this step may take up to one or two hours.
    The download is performed only once, so all next docker launches will take a few seconds, only sanity checks will take place.

**Install the VSLAM package**

.. code-block:: bash
    
    sudo apt update
    sudo apt install ros-humble-isaac-ros-visual-slam

**Build all packages**

.. code-block:: bash

    cd $ISAAC_ROS_WS
    source ./install/setup.bash
 
    cp ./src/isaac_ros_common/isaac_ros_rosbag_utils/isaac_ros_rosbag_utils/__init__.py ./src/isaac_ros_common/isaac_ros_rosbag_utils/isaac_ros_rosbag_utils/scripts/
 
    colcon build