#!/usr/bin/env python3
"""Reactive wander: drive forward while /scan is clear ahead, else turn until clear."""

import math

from geometry_msgs.msg import Twist, TwistStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def front_distance(scan, half_angle, method='mean', percentile=10.0, center=0.0):
    """Return (distance, valid_fraction) for the sector center +/- half_angle (rad).

    +inf readings (no return within range) count as range_max; NaN and
    readings below range_min are dropped as unknown.
    """
    vals = []
    total = 0
    for i, r in enumerate(scan.ranges):
        a = scan.angle_min + i * scan.angle_increment - center
        a = math.atan2(math.sin(a), math.cos(a))
        if abs(a) > half_angle:
            continue
        total += 1
        if math.isinf(r) and r > 0:
            vals.append(scan.range_max)
        elif math.isfinite(r) and scan.range_min <= r <= scan.range_max:
            vals.append(r)
    if total == 0 or not vals:
        return 0.0, 0.0
    vals.sort()
    if method == 'min':
        d = vals[0]
    elif method == 'percentile':
        d = vals[min(len(vals) - 1, int(len(vals) * percentile / 100.0))]
    else:
        d = sum(vals) / len(vals)
    return d, len(vals) / total


class Wander(Node):
    def __init__(self):
        super().__init__('wander')
        p = self.declare_parameter
        self.scan_topic = p('scan_topic', 'scan').value
        cmd_topic = p('cmd_vel_topic', 'cmd_vel').value
        self.use_stamped = p('use_stamped', False).value
        self.half_angle = math.radians(p('front_angle_deg', 20.0).value)
        self.method = p('method', 'mean').value
        self.percentile = p('percentile', 10.0).value
        self.clear = p('clear_distance', 1.0).value
        self.hyst = p('clear_hysteresis', 0.3).value
        self.min_valid = p('min_valid_fraction', 0.3).value
        self.v = p('linear_speed', 0.2).value
        self.w = p('angular_speed', 0.5).value
        self.timeout = p('scan_timeout', 0.5).value
        rate = p('rate', 10.0).value

        if self.method not in ('mean', 'min', 'percentile'):
            raise ValueError(f"method must be mean|min|percentile, got '{self.method}'")

        self.scan = None
        self.scan_time = None
        self.turn_dir = 0.0  # 0 = driving, +1 left, -1 right

        msg_type = TwistStamped if self.use_stamped else Twist
        self.pub = self.create_publisher(msg_type, cmd_topic, 10)
        self.create_subscription(
            LaserScan, self.scan_topic, self.on_scan, qos_profile_sensor_data)
        self.create_timer(1.0 / rate, self.step)
        self.get_logger().info(
            f'wander: {self.scan_topic} -> {cmd_topic} '
            f'({"TwistStamped" if self.use_stamped else "Twist"}), '
            f'method={self.method}, clear>{self.clear} m')

    def on_scan(self, msg):
        self.scan = msg
        self.scan_time = self.get_clock().now()

    def publish(self, vx, wz):
        if self.use_stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist.linear.x = vx
            msg.twist.angular.z = wz
        else:
            msg = Twist()
            msg.linear.x = vx
            msg.angular.z = wz
        self.pub.publish(msg)

    def side_room(self, side):
        """Mean free distance in the sector beyond the front window on one side."""
        d, _ = front_distance(self.scan, self.half_angle, 'mean',
                              center=side * 2.0 * self.half_angle)
        return d

    def step(self):
        if self.scan is None:
            return
        age = (self.get_clock().now() - self.scan_time).nanoseconds * 1e-9
        if age > self.timeout:
            self.turn_dir = 0.0
            self.publish(0.0, 0.0)
            return

        dist, valid = front_distance(
            self.scan, self.half_angle, self.method, self.percentile)
        blocked = valid < self.min_valid
        threshold = self.clear + (self.hyst if self.turn_dir else 0.0)

        if not blocked and dist > threshold:
            self.turn_dir = 0.0
            self.publish(self.v, 0.0)
            return

        if self.turn_dir == 0.0:
            # Latch a direction toward the side with more room to avoid dithering
            self.turn_dir = 1.0 if self.side_room(1.0) >= self.side_room(-1.0) else -1.0
            self.get_logger().info(
                f'blocked (front={dist:.2f} m, valid={valid:.0%}), '
                f'turning {"left" if self.turn_dir > 0 else "right"}')
        self.publish(0.0, self.turn_dir * self.w)


def main():
    rclpy.init()
    node = Wander()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish(0.0, 0.0)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
