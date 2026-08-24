import os
import sys

import rclpy
import yaml
from rclpy.node import Node
from sensor_msgs.msg import Image

from ad_r1m_perception_video.zmq_bridge import FrameSubscriber


class PerceptionPublisher(Node):
    def __init__(self, config_path=None):
        super().__init__('perception_publisher')

        if config_path is None:
            pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(pkg_dir, 'config', 'pipeline.yaml')

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        params = config['perception_node']['ros__parameters']
        bev_topic = params.get('bev', {}).get('publish_topic', '/perception/bev')
        self.floor_topic_base = params.get('floor', {}).get('publish_topic', '/perception/floor_mask')

        self.bev_pub = self.create_publisher(Image, bev_topic, 10)
        self.mask_pubs = {}

        self.subscriber = FrameSubscriber()

        self.timer = self.create_timer(1.0 / 30, self.tick)
        self.get_logger().info(f'PerceptionPublisher started — BEV on {bev_topic}')

    def tick(self):
        received = self.subscriber.recv()
        if received is None:
            return
        _, frames = received

        bev = frames.get('bev_frame')
        if bev is not None:
            msg = self._numpy_to_image_msg(bev, 'bgr8')
            self.bev_pub.publish(msg)

        for name, mask in frames.items():
            if not name.startswith('floor_mask_'):
                continue
            cam_key = name[len('floor_mask_'):]

            if cam_key not in self.mask_pubs:
                self.mask_pubs[cam_key] = self.create_publisher(
                    Image, f'{self.floor_topic_base}/{cam_key}', 10
                )
            msg = self._numpy_to_image_msg(mask, 'mono8')
            self.mask_pubs[cam_key].publish(msg)

    def _numpy_to_image_msg(self, array, encoding):
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.height = array.shape[0]
        msg.width = array.shape[1]
        msg.encoding = encoding
        msg.is_bigendian = False
        if array.ndim == 3:
            msg.step = array.shape[1] * array.shape[2]
        else:
            msg.step = array.shape[1]
        msg.data = array.tobytes()
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.subscriber.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
