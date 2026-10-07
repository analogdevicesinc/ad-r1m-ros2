#!/usr/bin/env python3
"""
Hardware-in-the-loop yaw controller for the AD-R1M simulation.

Subscribes to a real IMU for yaw setpoint and to the Gazebo diff-drive
odometry for yaw feedback, then publishes angular cmd_vel so the
simulated robot tracks the physical IMU orientation.  Forward/backward
motion comes from keyboard input (W/S keys) read in a background thread.

Published on the twist_mux "hil" channel so it can coexist with other
velocity sources.
"""

import math
import sys
import termios
import threading
import tty

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu

try:
    from tf_transformations import euler_from_quaternion
except ImportError:
    def euler_from_quaternion(q):
        """Minimal yaw-only fallback so the node runs without tf_transformations."""
        x, y, z, w = q
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        return (0.0, 0.0, yaw)


def _normalize_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


def _yaw_from_quaternion(q) -> float:
    _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
    return yaw


class ImuHilController(Node):

    # How long a W/S key-press drives forward/backward before auto-stopping (seconds)
    KEY_PULSE_DURATION = 0.3

    def __init__(self):
        super().__init__('imu_hil_controller')

        # ── Declare parameters (overridable via config YAML) ──
        self.declare_parameter('imu_topic', '/imu/data')
        self.declare_parameter('odom_topic', 'diff_drive_controller/odom')
        self.declare_parameter('cmd_vel_topic', 'cmd_vel_hil')
        self.declare_parameter('kp', 2.0)
        self.declare_parameter('max_angular_vel', 1.5)
        self.declare_parameter('linear_speed', 0.25)
        self.declare_parameter('control_rate', 50.0)
        self.declare_parameter('log_rate', 1.0)

        imu_topic = self.get_parameter('imu_topic').value
        odom_topic = self.get_parameter('odom_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.kp = self.get_parameter('kp').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value
        self.linear_speed = self.get_parameter('linear_speed').value
        control_rate = self.get_parameter('control_rate').value
        log_rate = self.get_parameter('log_rate').value

        # ── State ──
        self._imu_yaw = None
        self._sim_yaw = 0.0
        self._linear_x = 0.0
        self._linear_x_deadline = 0.0
        self._last_error = 0.0
        self._last_cmd_az = 0.0
        self._imu_received = False
        self._odom_received = False
        self._running = True

        # ── QoS for real IMU (often best-effort from micro-ROS / Madgwick) ──
        imu_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10,
        )

        # ── Subscribers ──
        self.create_subscription(Imu, imu_topic, self._imu_cb, imu_qos)
        self.create_subscription(Odometry, odom_topic, self._odom_cb, 10)

        # ── Publisher ──
        self._cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)

        # ── Control loop timer ──
        self._timer = self.create_timer(1.0 / control_rate, self._control_loop)

        # ── Periodic status log timer ──
        self._log_timer = self.create_timer(1.0 / log_rate, self._log_status)

        # ── Keyboard thread ──
        self._key_thread = threading.Thread(target=self._key_reader, daemon=True)
        self._key_thread.start()

        self.get_logger().info('--- HIL Controller Configuration ---')
        self.get_logger().info(f'  Subscribing IMU orientation : {imu_topic}')
        self.get_logger().info(f'  Subscribing sim odometry    : {odom_topic}')
        self.get_logger().info(f'  Publishing cmd_vel          : {cmd_vel_topic}')
        self.get_logger().info(f'  Kp={self.kp}  max_w={self.max_angular_vel}  '
                               f'lin_speed={self.linear_speed}')
        self.get_logger().info(f'  Control rate: {control_rate} Hz  '
                               f'Log rate: {log_rate} Hz')
        self.get_logger().info('------------------------------------')
        self.get_logger().info('Keyboard: W/S = nudge fwd/bwd, SPACE = stop, Q = quit')

    # ── Callbacks ──

    def _imu_cb(self, msg: Imu):
        self._imu_yaw = _yaw_from_quaternion(msg.orientation)
        if not self._imu_received:
            self._imu_received = True
            self.get_logger().info('First IMU orientation message received')

    def _odom_cb(self, msg: Odometry):
        self._sim_yaw = _yaw_from_quaternion(msg.pose.pose.orientation)
        if not self._odom_received:
            self._odom_received = True
            self.get_logger().info('First sim odometry message received')

    # ── Periodic status log ──

    def _log_status(self):
        ref_deg = math.degrees(self._imu_yaw) if self._imu_yaw is not None else float('nan')
        sim_deg = math.degrees(self._sim_yaw)
        err_deg = math.degrees(self._last_error)
        self.get_logger().info(
            f'ref={ref_deg:+7.1f}°  sim={sim_deg:+7.1f}°  '
            f'err={err_deg:+6.1f}°  cmd_az={self._last_cmd_az:+5.2f}  '
            f'lin={self._linear_x:+.2f}  '
            f'[IMU:{"OK" if self._imu_received else "WAIT"}  '
            f'ODOM:{"OK" if self._odom_received else "WAIT"}]'
        )

    # ── Control loop ──

    def _control_loop(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if now > self._linear_x_deadline:
            self._linear_x = 0.0

        twist = Twist()
        twist.linear.x = self._linear_x

        if self._imu_yaw is not None:
            error = _normalize_angle(self._imu_yaw - self._sim_yaw)
            angular_z = self.kp * error
            angular_z = max(-self.max_angular_vel,
                            min(self.max_angular_vel, angular_z))
            twist.angular.z = angular_z
            self._last_error = error
            self._last_cmd_az = angular_z

        self._cmd_pub.publish(twist)

    # ── Keyboard reader (runs in a daemon thread) ──

    def _key_reader(self):
        if not sys.stdin.isatty():
            self.get_logger().warn(
                'stdin is not a TTY — keyboard control disabled. '
                'Run in a terminal for W/S/Q input.'
            )
            return

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while self._running:
                ch = sys.stdin.read(1).lower()
                if ch == 'w':
                    self._linear_x = self.linear_speed
                    self._linear_x_deadline = (
                        self.get_clock().now().nanoseconds * 1e-9
                        + self.KEY_PULSE_DURATION
                    )
                elif ch == 's':
                    self._linear_x = -self.linear_speed
                    self._linear_x_deadline = (
                        self.get_clock().now().nanoseconds * 1e-9
                        + self.KEY_PULSE_DURATION
                    )
                elif ch == ' ':
                    self._linear_x = 0.0
                    self._linear_x_deadline = 0.0
                elif ch == 'q':
                    self._running = False
                    rclpy.shutdown()
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def destroy_node(self):
        self._running = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ImuHilController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
