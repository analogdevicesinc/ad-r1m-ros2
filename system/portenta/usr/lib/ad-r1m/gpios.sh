#!/bin/bash

sudo modprobe i2c-dev
echo 165 | sudo tee /sys/class/gpio/unexport
echo 166 | sudo tee /sys/class/gpio/unexport
echo 165 | sudo tee /sys/class/gpio/export
echo 166 | sudo tee /sys/class/gpio/export
