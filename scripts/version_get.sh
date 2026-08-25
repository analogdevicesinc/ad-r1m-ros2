#!/bin/bash

# Copyright (c) 2026 Analog Devices Inc.
#
# SPDX-License-Identifier: Apache-2.0

# Point of access for the current version across all component types.
# Reads multiple "sources of truth" for the project versions, preprocesses them,
# and outputs a number of KEY=VALUE lines interpretable as shell commands.
#
# Use in other scripts:
#
#     eval $(scripts/version_get.sh)
#
# Maintainers must keep this script up to date with the versioning policy.

## Version info of latest git tag ##############################################

LATEST_TAG=$(git describe --no-abbrev --tags)

LATEST_MAJOR="$(sed -nE 's/^([0-9]+).([0-9]+).([0-9]+)(-(.+))?$/\1/p' <<<"$LATEST_TAG")"
LATEST_MINOR="$(sed -nE 's/^([0-9]+).([0-9]+).([0-9]+)(-(.+))?$/\2/p' <<<"$LATEST_TAG")"
LATEST_PATCH="$(sed -nE 's/^([0-9]+).([0-9]+).([0-9]+)(-(.+))?$/\3/p' <<<"$LATEST_TAG")"
LATEST_LABEL="$(sed -nE 's/^([0-9]+).([0-9]+).([0-9]+)(-(.+))?$/\5/p' <<<"$LATEST_TAG")"
LATEST_NUMERIC="${LATEST_MAJOR}.${LATEST_MINOR}.${LATEST_PATCH}"
LATEST_VERSION="${LATEST_NUMERIC}${LATEST_LABEL:+-$LATEST_LABEL}"

echo LATEST_MAJOR="${LATEST_MAJOR}"
echo LATEST_MINOR="${LATEST_MINOR}"
echo LATEST_PATCH="${LATEST_PATCH}"
echo LATEST_LABEL="${LATEST_LABEL}"
echo LATEST_NUMERIC="${LATEST_NUMERIC}"
echo LATEST_VERSION="${LATEST_VERSION}"

## Differences between latest git tag and HEAD #################################

COMMITS_SINCE_LATEST=$(git rev-list "$LATEST_TAG"..HEAD | wc -l)
COMMIT_DATETIME=$(git show --no-patch --format=%ci HEAD)
COMMIT_DATE=$(date -u +'%Y-%m-%d' -d "$COMMIT_DATETIME")

echo COMMITS_SINCE_LATEST="${COMMITS_SINCE_LATEST}"
echo COMMIT_DATE="${COMMIT_DATE}"

## ROS packages version ########################################################
# Release: 1.2.3
# Prerelease: 1.2.3
# Can't represent pre-release info. Always latest release, even if stale.

VERSION_ROS="${LATEST_NUMERIC}"

echo VERSION_ROS="${VERSION_ROS}"

## Docker image tags ###########################################################
# Release:    1.2.3, 1.2, 1
# Prerelease: 1.2.3-next, 1.2-next, 1-next

DOCKER_SUFFIX=
if [ "$COMMITS_SINCE_LATEST" -ne 0 ]; then
    DOCKER_SUFFIX=-next
fi

VERSION_DOCKER=(
    "${LATEST_MAJOR}.${LATEST_MINOR}.${LATEST_PATCH}${DOCKER_SUFFIX}"
    "${LATEST_MAJOR}.${LATEST_MINOR}${DOCKER_SUFFIX}"
    "${LATEST_MAJOR}${DOCKER_SUFFIX}"
)

echo VERSION_DOCKER="\"${VERSION_DOCKER[@]}\""

## Debian package version ######################################################
# Release: 1.2.3-1
# Prerelease: 1.2.4~git20261225.2359.a1b2c3d-1
#
# Prerelease base version (e.g. 1.2.4) relies on maintainer having previously
# added an entry (distro UNRELEASED) to the top of the changelog for the
# upcoming version.

VERSION_DEBIAN="$(dpkg-parsechangelog -l packaging/debian/changelog -S version)"

VERSION_DEBIAN_BASE="${VERSION_DEBIAN%-1}"

DEBIAN_SUFFIX=
if [ "$COMMITS_SINCE_LATEST" != 0 ]; then
    DEBIAN_SUFFIX="~git$(date -u +'%Y%m%d.%H%M' -d "$COMMIT_DATETIME").$(git rev-parse --short HEAD)"
fi

VERSION_DEBIAN="${VERSION_DEBIAN_BASE}${DEBIAN_SUFFIX}-1"
echo VERSION_DEBIAN="${VERSION_DEBIAN}"
