#!/bin/bash
mkdir -p /run/dbus /run/avahi-daemon
dbus-daemon --system --fork
avahi-daemon --no-drop-root --daemonize
echo "Avahi + DBus started"
