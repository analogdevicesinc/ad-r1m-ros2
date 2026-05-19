#!/bin/bash

if [ -e /dev/video0 ]; then
    media-ctl --link "'adsd3500 2-0038':0->'csis-32e30000.mipi_csi':0[1]"

    media-ctl -d /dev/media0 --set-v4l2 '"adsd3500 2-0038":0[fmt:SBGGR8_1X8/2560x512]'
    media-ctl -d /dev/media0 --set-v4l2 '"csis-32e30000.mipi_csi":1[fmt:SBGGR8_1X8/2560x512]'
    media-ctl -d /dev/media0 --set-v4l2 '"csi":1[fmt:SBGGR8_1X8/2560x512]'
fi

echo "Done configuring media-ctl"
