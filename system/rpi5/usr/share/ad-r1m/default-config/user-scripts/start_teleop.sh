#!/usr/bin/env bash
pushd $(dirname $0)
default_ROBOT_NAMESPACE=$(hostname)
default_ROBOT_NAMESPACE=${default_ROBOT_NAMESPACE//-/_}
export ROBOT_NAMESPACE=${ROBOT_NAMESPACE:-$default_ROBOT_NAMESPACE}
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_zenoh_cpp}
docker compose run --rm teleop_autonomous
