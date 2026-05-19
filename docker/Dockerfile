# Build arguments
ARG ROS_DISTRO=humble
ARG FROM_IMAGE=ros:$ROS_DISTRO
ARG OVERLAY_WS=/ros2_ws
ARG BUILD_PACKAGES=ad_r1m_robot

####################################################################################################
# common stage:
#   Add common stuff like python3-pip, rosdep update, which are needed by all future stages.
#
#   Internal: users shouldn't use this as a target; used for better multi-stage caching logic.

FROM $FROM_IMAGE AS common
ARG OVERLAY_WS
ARG ROS_DISTRO

ENV OVERLAY_WS=$OVERLAY_WS

WORKDIR $OVERLAY_WS

RUN apt-get update && \
    apt-get install -y \
        python3-pip

RUN echo yaml file:///rosdep.yaml > /etc/ros/rosdep/sources.list.d/01-ad_r1m.list
COPY rosdep.yaml /rosdep.yaml
RUN rosdep update --rosdistro $ROS_DISTRO

RUN --mount=type=secret,id=GH_TOKEN,env=GH_TOKEN if [ "$GH_TOKEN" ]; then git config --global url."https://${GH_TOKEN}@github.com".insteadOf "https://github.com"; fi


####################################################################################################
# depcacher stage:
#   Copies the entire source tree and any source dependencies. Synthesizes a list of apt and pip
#   dependencies for both the build and execution. These will be cached!
#
#   Internal: users shouldn't use this as a target; used for better multi-stage caching logic.

FROM common AS depcacher
ARG BUILD_PACKAGES

ENV DEBIAN_FRONTEND=noninteractive

RUN cat <<EOF > /etc/apt/apt.conf.d/docker-clean-with-cache
APT::Install-Recommends "false";
APT::Install-Suggests "false";
Binary::apt::APT::Keep-Downloaded-Packages "true";
EOF

RUN mkdir -p src/ad_r1m_ros2/

# First clone external sources -- keep this as separate as possible from the other sources,
# so we don't trigger a clone in every build
COPY repos.vcs src/ad_r1m_ros2/
RUN vcs import src < src/ad_r1m_ros2/repos.vcs

# ...then copy everything else
COPY ./ src/ad_r1m_ros2/

# Parse dependencies, split by {build,exec} and {apt,pip}
RUN bash -e <<'EOF'
export BUILD_PACKAGES_PATHS=$(colcon list -p --packages-up-to ${BUILD_PACKAGES})
export PIP_BREAK_SYSTEM_PACKAGES=1
declare -A types=(
  [exec]="--dependency-types=exec"
  [build]="")
for type in "${!types[@]}"; do
    # apt-get deps:
    rosdep install -y -r --from-paths $BUILD_PACKAGES_PATHS --ignore-src --reinstall --simulate ${types[$type]} \
        | grep 'apt-get install ' \
        | awk '{print $NF;}' \
        | sort -u > /tmp/${type}_apt.txt
    # pip deps:
    rosdep install -y -r --from-paths $BUILD_PACKAGES_PATHS --ignore-src --reinstall --simulate ${types[$type]} \
        | grep -E 'pip3? install ' \
        | awk '{print $NF;}' \
        | sort -u > /tmp/${type}_pip.txt
done
EOF

# Add a few extra exec dependencies that are currently not brought by rosdep (rmws "just to be sure")
RUN cat <<EOF >>/tmp/exec_apt.txt
gpiod
ros-$ROS_DISTRO-rmw-fastrtps-cpp
ros-$ROS_DISTRO-rmw-cyclonedds-cpp
ros-$ROS_DISTRO-rmw-zenoh-cpp
EOF
RUN sort -u -o /tmp/exec_apt.txt /tmp/exec_apt.txt


####################################################################################################
# build_common:
#   Install build and development dependencies.
#
#   Internal: users shouldn't use this as a target; used for better multi-stage caching logic.

FROM common AS build_common

ENV CCACHE_DIR=/ccache

# Install build deps
COPY --from=depcacher /tmp/build_*.txt /tmp/

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/etc/apt/apt.conf.d,from=depcacher,source=/etc/apt/apt.conf.d,readonly \
    --mount=type=cache,target=/var/lib/apt/lists,from=depcacher,source=/var/lib/apt/lists,readonly \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    < /tmp/build_apt.txt xargs apt-get install -y \
        ccache \
        can-utils \
        gdb \
        vim

ENV DEBIAN_FRONTEND=

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r /tmp/build_pip.txt

####################################################################################################
# devcontainer stage:
#   User-facing development container with nothing built yet. Doesn't copy sources, those should be
#   mounted into the workspace so changes are persisted outside of the devcontainer. Users enter the
#   devcontainer and later build packages themselves.

FROM build_common AS devcontainer

# Install exec deps
COPY --from=depcacher /tmp/exec_*.txt /tmp/

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/etc/apt/apt.conf.d,from=depcacher,source=/etc/apt/apt.conf.d,readonly \
    --mount=type=cache,target=/var/lib/apt/lists,from=depcacher,source=/var/lib/apt/lists,readonly \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    < /tmp/exec_apt.txt xargs apt-get install -y

ENV DEBIAN_FRONTEND=

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r /tmp/exec_pip.txt

# Build an empty workspace so we get a install/setup.bash
# No need to mount caches or use any mixins here
RUN colcon build

# Prepare entrypoint for user-facing container
RUN sed --in-place --expression \
      '$isource "${OVERLAY_WS}/install/setup.bash"' \
      /ros_entrypoint.sh

# Prepare source statements for devcontainer -- entrypoint doesn't matter
RUN tee -a ~/.bashrc <<'EOF'
source /opt/ros/$ROS_DISTRO/setup.bash
source ${OVERLAY_WS}/install/setup.bash
EOF

####################################################################################################
# builder stage:
#   Copies sources, builds.
#
#   Internal: users shouldn't use this as a target; used for better multi-stage caching logic.

FROM build_common AS builder
ARG ROS_DISTRO
ARG BUILD_PACKAGES

# Copy both our sources and sources pulled with vcs
COPY --from=depcacher $OVERLAY_WS/src ./src

# Build
RUN --mount=type=cache,target=/ccache/ . /opt/ros/$ROS_DISTRO/setup.sh && \
    colcon build \
      --packages-up-to ${BUILD_PACKAGES} \
      --mixin rel-with-deb-info \
      --mixin ccache
RUN --mount=type=cache,target=/ccache/ ccache -s


####################################################################################################
# dev stage:
#   User-facing runtime container with both built packages as well as dev tools. Large, but useful
#   when you need to jump in and edit, rebuild, debug, etc.
 
FROM builder AS dev

# Install exec deps
COPY --from=depcacher /tmp/exec_*.txt /tmp/

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/etc/apt/apt.conf.d,from=depcacher,source=/etc/apt/apt.conf.d,readonly \
    --mount=type=cache,target=/var/lib/apt/lists,from=depcacher,source=/var/lib/apt/lists,readonly \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    < /tmp/exec_apt.txt xargs apt-get install -y

ENV DEBIAN_FRONTEND=

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r /tmp/exec_pip.txt

# Prepare entrypoint for user-facing container
RUN sed --in-place --expression \
      '$isource "${OVERLAY_WS}/install/setup.bash"' \
      /ros_entrypoint.sh


####################################################################################################
# runner stage:
#   User-facing container for deployed robot runtime. As thin as possible, with no dev tools,
#   sources, etc.

FROM $FROM_IMAGE-ros-core AS runner
ARG OVERLAY_WS

ENV OVERLAY_WS=$OVERLAY_WS

WORKDIR $OVERLAY_WS

# Install exec deps
COPY --from=depcacher /tmp/exec_*.txt /tmp/

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/etc/apt/apt.conf.d,from=depcacher,source=/etc/apt/apt.conf.d,readonly \
    --mount=type=cache,target=/var/lib/apt/lists,from=depcacher,source=/var/lib/apt/lists,readonly \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    </tmp/exec_apt.txt xargs apt-get install -y \
        python3-pip

ENV DEBIAN_FRONTEND=

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r /tmp/exec_pip.txt

# Copy built overlay
COPY --from=builder $OVERLAY_WS/install $OVERLAY_WS/install

# Prepare entrypoint for user-facing container
RUN sed --in-place --expression \
      '$isource "${OVERLAY_WS}/install/setup.bash"' \
      /ros_entrypoint.sh
