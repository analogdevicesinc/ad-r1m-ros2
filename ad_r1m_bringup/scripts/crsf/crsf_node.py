#! /usr/bin/env python3
import rclpy
from rclpy.node import Node
from crsf_parser import CRSFParser
from crsf_parser.payloads import PacketsTypes
from crsf_parser.handling import crsf_build_frame
from std_msgs.msg import Bool
from canopen_interfaces.srv import CORead  # SDO read service
from geometry_msgs.msg import TwistStamped, Twist
from std_srvs.srv import Trigger
from serial import Serial
import math


class CRSFNode(Node):
    """
    Listens to ExpressLRS CRSF transceiver.

    ## Joystick

    Publishes right joystick.

    Topics:
    - `/cmd_vel_joy_unstamped` Twist
    - `/cmd_vel_joy` TwistStamped

    Params:
    - `poll_rate` : Rate at which to check RC control values
    - `min_joy_pos` : Minimum joystick deviation from (0,0) to publish cmd_vel
    - `max_vel` : Maximum linear velocity
    - `max_rot` : Maximum angular velocity

    ## Battery telemetry

    Reports current battery voltage (read via SDO) to CRSF.

    Params:
    - `battery_poll_period` : Period between battery voltage measurements
    - `battery_sdo_service` : Service to use for reading battery voltage SDO

    ## Killswitch

    Switch SA acts as a killswitch.

    Params:
    - `kill_sequence` : List of services to call on killswitch enable
    - `init_sequence` : List of services to call on killswitch disable

    """

    def __init__(self):
        super().__init__('crsf')

        self.declare_parameter('serial_device', '/dev/ttyCRSF')
        self.declare_parameter('poll_rate', 20)
        self.declare_parameter('min_joy_pos', 0.1)
        self.declare_parameter('max_vel', 0.5)
        self.declare_parameter('max_rot', 1.0)
        self.declare_parameter('battery_poll_period', 1)
        self.declare_parameter('battery_sdo_service', 'drive_left/sdo_read')
        self.declare_parameter('battery_cell_min_voltage', 3.0)
        self.declare_parameter('battery_cell_max_voltage', 4.2)
        self.declare_parameter('battery_cell_count', 3)
        self.declare_parameter('battery_capacity_mah', 6000)
        self.declare_parameter(
            'kill_sequence', ['drive_left/halt', 'drive_right/halt'])
        self.declare_parameter(
            'init_sequence', ['drive_left/init', 'drive_right/init'])

        self.serial_device = self.get_parameter('serial_device').value
        self.poll_rate = self.get_parameter('poll_rate').value
        self.min_joy_pos = self.get_parameter('min_joy_pos').value
        self.max_vel = self.get_parameter('max_vel').value
        self.max_rot = self.get_parameter('max_rot').value
        self.battery_poll_period = self.get_parameter(
            'battery_poll_period').value
        self.battery_sdo_service = self.get_parameter(
            'battery_sdo_service').value
        self.battery_cell_min_voltage = self.get_parameter(
            'battery_cell_min_voltage').value
        self.battery_cell_max_voltage = self.get_parameter(
            'battery_cell_max_voltage').value
        self.battery_cell_count = self.get_parameter('battery_cell_count').value
        self.battery_capacity_mah = self.get_parameter('battery_capacity_mah').value
        self.kill_sequence = self.get_parameter('kill_sequence').value
        self.init_sequence = self.get_parameter('init_sequence').value

        # Publishers
        self.cmd_publisher = self.create_publisher(
            TwistStamped, 'cmd_vel_joy', 1)
        self.cmdu_publisher = self.create_publisher(
            Twist, 'cmd_vel_joy_unstamped', 1)
        self.kill_publisher = self.create_publisher(Bool, 'killswitch', 1)

        # Timers
        self.fast_timer = self.create_timer(
            1.0 / self.poll_rate, self.fast_timer_callback)

        if self.battery_poll_period > 0 and self.battery_sdo_service:
            self.battery_timer = self.create_timer(
                self.battery_poll_period, self.battery_timer_callback)

            # Service client for reading supply voltage
            self.cli = self.create_client(CORead, self.battery_sdo_service)
        else:
            self.battery_timer = None
            self.cli = None

        # Service clients to stop / start the motors
        self.stop_services = [
            self.create_client(
                Trigger,
                service) for service in self.kill_sequence if service]
        self.start_services = [
            self.create_client(
                Trigger,
                service) for service in self.init_sequence if service]
        self.service_call_queue = []

        # Wait for services to become available
        for cli in ([self.cli] if self.cli else []) + self.stop_services + self.start_services:
            self.get_logger().info(f'Waiting for service {cli.srv_name}')
            while not cli.wait_for_service(timeout_sec=5.0):
                self.get_logger().info(f'Waiting for service {cli.srv_name}')

        # CRSF setup
        try:
            self.serial = Serial(self.serial_device, 420000, timeout=0.01)
        except Exception as e:
            self.get_logger().fatal(f'Failed to open serial device {self.serial_device}: {e}')
            raise SystemExit(1)

        self.channels = []
        self.channels_decoded = []

        # Queued up bytes from serial
        self.incoming = bytearray()
        def crsf_callback(
            frame, status): return self.crsf_callback(frame, status)
        self.crsf_parser = CRSFParser(crsf_callback)
        self.empty_crsf_count = 0

        # init -[kill switch on]-> kill -[kill switch off]-> run -[kill switch
        # on]-> kill
        self.state = 'init'
        self.previous_was_static = True

    def service_queue_process(self, result):
        if not self.service_call_queue:
            return

        self.get_logger().info(f'{self.service_call_queue=}')
        next_req, self.service_call_queue = self.service_call_queue[0], self.service_call_queue[1:]
        self.get_logger().info(f'{next_req=}')
        cli, req = next_req
        self.get_logger().info(f'Calling service {cli.srv_name}')

        f = cli.call_async(req)
        f.add_done_callback(lambda res: self.service_queue_process(res))

    def queue_up_service_calls(self, cli_req_pairs):
        self.get_logger().info(
            f'Queueing service call sequence {[c.srv_name for c,r in cli_req_pairs]}')
        if not self.service_call_queue:
            self.service_call_queue.extend(cli_req_pairs)
            self.service_queue_process(None)
        else:
            self.service_call_queue.extend(cli_req_pairs)

    def battery_timer_callback(self):
        # Called every second to request the batery voltage via SDO
        req = CORead.Request()
        req.index = 0x2122  # SUPPLY_VOLTAGE
        req.subindex = 0

        self.get_logger().debug('Requesting battery')
        future = self.cli.call_async(req)
        future.add_done_callback(
            lambda result: self.battery_value_callback(result))

    def battery_value_callback(self, future):
        # Called when we get an SDO response for SUPPLY_VOLTAGE
        res = future.result()
        if not future.done() or not res.success:
            self.get_logger().error("Couldn't get battery voltage")
            return

        v = res.data * 0.1
        v_per_cell = v * 0.1 / self.battery_cell_count
        voltage_range = self.battery_cell_max_voltage - self.battery_cell_min_voltage
        rem = (v_per_cell - self.battery_cell_min_voltage) / voltage_range * 100
        rem = max(0, min(100, rem))
        self.get_logger().info(f'battery {v:.1f} V')

        battery_frame = crsf_build_frame(PacketsTypes.BATTERY_SENSOR, {
            'voltage': int(v * 10 + 0.5),
            'current': 0,
            'capacity': self.battery_capacity_mah,
            'remaining': int(rem)
        })

        self.serial.write(battery_frame)

    def crsf_callback(self, frame, status):
        # Called as part of fast_timer_callback every processed CRSF frame
        # print(f'{frame=} {status=}')
        if frame.header.type == PacketsTypes.RC_CHANNELS_PACKED:
            self.channels = list(frame.payload.channels)[::-1][:10]
            self.channels_decoded = [
                int(1500.5 + 5 / 8 * (x - 992)) for x in self.channels]

    def fast_timer_callback(self):
        # Always process CRSF stream
        crsf_bytes = self.serial.read(10240)
        if crsf_bytes:
            self.empty_crsf_count = 0
            self.incoming.extend(crsf_bytes)
            # self.get_logger().info(f'{self.incoming=}')

            # May call crsf_callback
            self.crsf_parser.parse_stream(self.incoming)
        else:
            self.empty_crsf_count += 1
            if self.empty_crsf_count > 50 and self.state != 'kill':
                self.get_logger().error('Got 50 empty CRSF reads, shutting down for safety')
                self.enter_kill()
                self.channels = []
                return

        # Wait for initialization / deinitialization sequence to finish
        if self.service_call_queue:
            return

        # No channel data yet
        if not self.channels:
            return

        # Parse channels
        # rx, ry, lx, ly = x, y values of right / left stick
        # Map 1000..2000 to -100..100
        rx, ry, ly, lx, sa, sb, sc, sd, se, sf = [
            (x - 1500) / 5 for x in self.channels_decoded]
        # self.get_logger().info(f'{sa=} {sb=} {sc=} {sd=} {se=} {sf=}')

        if self.state == 'init':
            if sa > 0:
                self.enter_run()
                # self.get_logger().info(
                #    'Safety: Activate kill switch, so that deactivating it is intentional')
                # return
            else:
                self.enter_kill()

        if self.state == 'kill':
            if sa > 0:
                self.enter_run()
            else:
                return

        # Running
        if sa < 0:
            self.enter_kill()
            return

        # Dead zone
        if abs(rx / 100) < self.min_joy_pos:
            rx = 0
        if abs(ry / 100) < self.min_joy_pos:
            ry = 0

        if rx == 0 and ry == 0:
            if self.previous_was_static:
                return

            self.previous_was_static = True
        else:
            self.previous_was_static = False

        cmd = TwistStamped()
        cmd.header.frame_id = 'base_link'
        cmd.twist.linear.x = ry / 100 * self.max_vel
        cmd.twist.angular.z = -rx / 100 * self.max_rot
        self.get_logger().info(
            f'MANUAL:\t{cmd.twist.linear.x:.01f} m/s\t{cmd.twist.angular.z:.01f} rad/s')
        self.cmd_publisher.publish(cmd)
        self.cmdu_publisher.publish(cmd.twist)

    def enter_kill(self):
        self.state = 'kill'
        b = Bool()
        b.data = True
        self.kill_publisher.publish(b)
        self.get_logger().info('KILLSWITCH')

        twist = TwistStamped()  # Defaults to all zeros
        twist.header.frame_id = 'base_link'
        self.cmd_publisher.publish(twist)
        self.cmdu_publisher.publish(twist.twist)

        for cli in self.stop_services:
            # Stop asynchronously to ensure fast response
            cli.call_async(Trigger.Request())

    def enter_run(self):
        self.state = 'run'  # Will be shortly changed to run_manual or run_auto
        b = Bool()
        b.data = False
        self.kill_publisher.publish(b)
        self.get_logger().info('INITIALIZING')

        self.queue_up_service_calls(
            [(cli, Trigger.Request()) for cli in self.start_services])


def main(args=None):
    rclpy.init(args=args)

    crsf_node = CRSFNode()

    rclpy.spin(crsf_node)

    crsf_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
