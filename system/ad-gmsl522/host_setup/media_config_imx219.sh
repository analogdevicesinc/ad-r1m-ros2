#!/bin/bash

if [ -e /dev/video0 ]; then
    media-ctl -d /dev/media0 --set-v4l2 '"ser_0_ch_0":1[fmt:SRGGB10_1X10/1920x1080]'
    media-ctl -d /dev/media0 --set-v4l2 '"des_ch_0":0[fmt:SRGGB10_1X10/1920x1080]'
fi

if [ -e /dev/video1 ]; then
    media-ctl -d /dev/media0 --set-v4l2 '"ser_1_ch_0":1[fmt:SRGGB10_1X10/1920x1080]'
    media-ctl -d /dev/media0 --set-v4l2 '"des_ch_1":0[fmt:SRGGB10_1X10/1920x1080]'
fi

if [ -e /dev/video2 ]; then
    media-ctl -d /dev/media0 --set-v4l2 '"ser_2_ch_0":1[fmt:SRGGB10_1X10/1920x1080]'
    media-ctl -d /dev/media0 --set-v4l2 '"des_ch_2":0[fmt:SRGGB10_1X10/1920x1080]'
fi

if [ -e /dev/video3 ]; then
    media-ctl -d /dev/media0 --set-v4l2 '"ser_3_ch_0":1[fmt:SRGGB10_1X10/1920x1080]'
    media-ctl -d /dev/media0 --set-v4l2 '"des_ch_3":0[fmt:SRGGB10_1X10/1920x1080]'
fi

echo "Done configuriing media-ctl"
