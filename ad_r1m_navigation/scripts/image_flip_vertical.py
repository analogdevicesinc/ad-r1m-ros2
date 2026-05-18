#!/usr/bin/env python3
"""
Flips an image vertically (upside down correction).
Used when camera is mounted inverted but raw image is not corrected.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np


class ImageFlipVertical(Node):
    def __init__(self):
        super().__init__('image_flip_vertical')

        self.declare_parameter('input_topic', '/cam1/depth_image')
        self.declare_parameter('output_topic', '/cam1/depth_image_flipped')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        self.publisher = self.create_publisher(Image, output_topic, 10)
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            10
        )

        self.get_logger().info(
            f'Flipping images vertically: {input_topic} -> {output_topic}'
        )

    def image_callback(self, msg):
        # Determine bytes per pixel based on encoding
        if msg.encoding in ['mono8', '8UC1']:
            dtype = np.uint8
            channels = 1
        elif msg.encoding in ['mono16', '16UC1']:
            dtype = np.uint16
            channels = 1
        elif msg.encoding in ['rgb8', 'bgr8']:
            dtype = np.uint8
            channels = 3
        elif msg.encoding in ['rgba8', 'bgra8']:
            dtype = np.uint8
            channels = 4
        elif msg.encoding == '32FC1':
            dtype = np.float32
            channels = 1
        else:
            self.get_logger().warn(f'Unknown encoding: {msg.encoding}, passing through')
            self.publisher.publish(msg)
            return

        # Convert to numpy array
        if channels == 1:
            img = np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.width)
        else:
            img = np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.width, channels)

        # Flip vertically (upside down)
        img_flipped = np.flipud(img)

        # Create output message
        out_msg = Image()
        out_msg.header = msg.header
        out_msg.height = msg.height
        out_msg.width = msg.width
        out_msg.encoding = msg.encoding
        out_msg.is_bigendian = msg.is_bigendian
        out_msg.step = msg.step
        out_msg.data = img_flipped.tobytes()

        self.publisher.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImageFlipVertical()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
