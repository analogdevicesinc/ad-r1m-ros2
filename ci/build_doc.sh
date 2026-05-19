#!/usr/bin/env bash

set -eou pipefail

BASE_PATH=$(git rev-parse --show-toplevel)

echo "Installing dependencies"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y graphviz doxygen

echo "Generating the build directory"
mkdir -p "$BASE_PATH"/_build

echo "Building the docs using rosdoc2"
pushd "$BASE_PATH"/_build >/dev/null || exit

# Generate docs for the ad_r1m package which contains the main documentation
rosdoc2 build --package-path "$BASE_PATH/ad_r1m" --debug

popd >/dev/null
