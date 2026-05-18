#!/usr/bin/env python3
"""
Combined image preprocessing: flip vertically and fix encoding.
Reduces latency compared to chaining multiple nodes.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np


class ImagePreprocess(Node):
    def __init__(self):
        super().__init__('image_preprocess')

        self.declare_parameter('input_topic', '/cam1/ab_image')
        self.declare_parameter('output_topic', '/cam1/ab_image_processed')
        self.declare_parameter('flip_vertical', True)
        self.declare_parameter('target_encoding', '')  # Empty = keep original

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.flip_vertical = self.get_parameter('flip_vertical').value
        self.target_encoding = self.get_parameter('target_encoding').value

        self.publisher = self.create_publisher(Image, output_topic, 10)
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            10
        )

        self.get_logger().info(
            f'Preprocessing: {input_topic} -> {output_topic} '
            f'(flip={self.flip_vertical}, encoding={self.target_encoding or "keep"})'
        )

    def image_callback(self, msg):
        out_msg = Image()
        out_msg.header = msg.header
        out_msg.height = msg.height
        out_msg.width = msg.width
        out_msg.is_bigendian = msg.is_bigendian
        out_msg.step = msg.step

        # Fix encoding if needed (16UC1 -> mono16)
        if self.target_encoding:
            out_msg.encoding = self.target_encoding
        else:
            out_msg.encoding = msg.encoding

        # Flip if needed
        if self.flip_vertical:
            # Determine dtype
            if msg.encoding in ['mono8', '8UC1']:
                dtype = np.uint8
                channels = 1
            elif msg.encoding in ['mono16', '16UC1']:
                dtype = np.uint16
                channels = 1
            elif msg.encoding in ['rgb8', 'bgr8']:
                dtype = np.uint8
                channels = 3
            elif msg.encoding == '32FC1':
                dtype = np.float32
                channels = 1
            else:
                # Unknown encoding, just pass through with encoding fix
                out_msg.data = msg.data
                self.publisher.publish(out_msg)
                return

            # Flip
            if channels == 1:
                img = np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.width)
            else:
                img = np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.width, channels)

            img_flipped = np.flipud(img)
            out_msg.data = img_flipped.tobytes()
        else:
            out_msg.data = msg.data

        self.publisher.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImagePreprocess()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
