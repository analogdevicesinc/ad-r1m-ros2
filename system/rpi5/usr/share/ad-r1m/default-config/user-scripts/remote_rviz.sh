export ROS_NAMESPACE=ad_r1m_6
ROBOT_TCP_NAME=${ROS_NAMESPACE//_/-}

export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ZENOH_CONFIG_OVERRIDE="connect/endpoints=[\"tcp/${ROBOT_TCP_NAME}.local:7447\"];mode=\"client\""

ros2 run rviz2 rviz2 -d $(dirname $0)/../ad_r1m_base/rviz/main.rviz --ros-args -r /goal_pose:=/${ROS_NAMESPACE}/goal_pose -r /initialpose:=/${ROS_NAMESPACE}/initialpose
