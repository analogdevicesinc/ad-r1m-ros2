#!/usr/bin/env python3
"""
Republishes an image with corrected encoding.
Converts 16UC1 encoding label to mono16 for RTAB-Map compatibility.
The actual image data is unchanged - only the encoding label is fixed.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImageEncodingRepublisher(Node):
    def __init__(self):
        super().__init__('image_encoding_republisher')

        # Parameters
        self.declare_parameter('input_topic', '/cam1/ab_image')
        self.declare_parameter('output_topic', '/cam1/ab_image_mono')
        self.declare_parameter('target_encoding', 'mono16')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.target_encoding = self.get_parameter('target_encoding').value

        self.publisher = self.create_publisher(Image, output_topic, 10)
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            10
        )

        self.get_logger().info(
            f'Republishing {input_topic} -> {output_topic} '
            f'with encoding: {self.target_encoding}'
        )

    def image_callback(self, msg):
        # Create a copy with corrected encoding
        out_msg = Image()
        out_msg.header = msg.header
        out_msg.height = msg.height
        out_msg.width = msg.width
        out_msg.encoding = self.target_encoding  # Fix: 16UC1 -> mono16
        out_msg.is_bigendian = msg.is_bigendian
        out_msg.step = msg.step
        out_msg.data = msg.data

        self.publisher.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImageEncodingRepublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
