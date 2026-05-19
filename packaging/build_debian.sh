#!/usr/bin/env bash

# Move to repo root
REPO_BASE="$(realpath -m "$0/../../")"
pushd "$REPO_BASE"

# Get version suffix from CLI arg. Should be like:
# -1                     (for release builds)
# ~git20060102.abcdef0-1 (for nightly builds) -- default if none provided
# ~pre123                (for prerelease builds)
# See https://wiki.debian.org/Versioning

VERSION_SUFFIX="${1-$VERSION_SUFFIX}"
if [ -z "$VERSION_SUFFIX" ]; then
    VERSION_SUFFIX="~git$(date -u +'%Y%m%d.%H%M').$(git rev-parse --short HEAD)-1"
    echo "No version suffix argument provided, using nightly scheme:"
    echo "VERSION_SUFFIX=$VERSION_SUFFIX"
fi

VERSION=$(cat VERSION)
VERSION_FULL="${VERSION}${VERSION_SUFFIX}"
VERSION_FULL_NO_DEBREVISION="${VERSION_FULL%-*}" # Remove the -1 at the end
SOURCE_NAME=ad-r1m-system

echo "VERSION_FULL=$VERSION_FULL"

rm -r packaging/build
mkdir -p "packaging/build/$SOURCE_NAME"

cp -r packaging/debian "packaging/build/$SOURCE_NAME"
cp -r system "packaging/build/$SOURCE_NAME"
cp -r VERSION "packaging/build/$SOURCE_NAME"

pushd packaging/build
tar czf "${SOURCE_NAME}_${VERSION_FULL_NO_DEBREVISION}.orig.tar.gz" --exclude **/debian "$SOURCE_NAME"
popd

pushd "packaging/build/$SOURCE_NAME"
dch -b --newversion "$VERSION_FULL" ""
debuild
