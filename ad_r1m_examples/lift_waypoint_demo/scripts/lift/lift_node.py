#!/usr/bin/env python3

import time
from enum import IntEnum

from smbus3 import SMBus
import rclpy
from rclpy.node import Node
from ad_r1m_base.srv import LiftGPIO
import gpio as GPIO


class LifterCommand(IntEnum):
    NOOP = 0
    UP = 1
    DOWN = 2


class LifterStatus(IntEnum):
    NOOP = 0
    MOVING_UP = 1
    MOVING_DOWN = 2
    ARRIVED_UP = 3
    ARRIVED_DOWN = 4


class LiftNode(Node):
    def __init__(self):
        super().__init__('liftnode')
        self.i2cbus = SMBus(2)
        self.lifter_address = 0x60
        self.srv = self.create_service(
            LiftGPIO, 'elevator_to_robot', self.lift_callback)
        GPIO.setup(165, GPIO.OUT)
        GPIO.setup(166, GPIO.OUT)
        self.get_logger().info('LiftNode initialized.')

    def lift_callback(self, request, response):
        led = request.led_state
        cmd = request.lift_state
        print('Request.led_state: ', led)
        match led:
            case 0:
                GPIO.output(165, GPIO.LOW)
                GPIO.output(166, GPIO.LOW)
            case 1:
                GPIO.output(165, GPIO.HIGH)
                GPIO.output(166, GPIO.LOW)
            case 2:
                GPIO.output(165, GPIO.LOW)
                GPIO.output(166, GPIO.HIGH)
            case 3:
                GPIO.output(165, GPIO.HIGH)
                GPIO.output(166, GPIO.HIGH)

        print('Request.lift_state: ', cmd)
        match cmd:
            case 1:
                self.send_command(LifterCommand.UP)
                # self.wait_for_status(LifterStatus.ARRIVED_UP)
            case 2:
                self.send_command(LifterCommand.DOWN)
                # self.wait_for_status(LifterStatus.ARRIVED_DOWN)
            case 0:
                self.send_command(LifterCommand.NOOP)
        response.done = True
        return response

    def send_command(self, cmd: LifterCommand):
        self.i2cbus.write_byte(self.lifter_address, cmd.value)

    def wait_for_status(self, target_status: LifterStatus):
        while True:
            status = self.i2cbus.read_byte(self.lifter_address)
            if status == target_status.value:
                return
            time.sleep(0.1)

    def check_status(self, target_status: LifterStatus):
        status = self.i2cbus.read_byte(self.lifter_address)
        return int(status == target_status.value)


class LiftClientAsync(Node):
    def __init__(self):
        super().__init__('lift_client_async')
        self.cli = self.create_client(LiftGPIO, 'elevator_to_robot')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')
        self.req = LiftGPIO.Request()

    def send_request(self, request):
        self.req = request
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()


def main(args=None):
    rclpy.init(args=args)
    lift_node = LiftNode()
    print('Lift node is running...')
    try:
        rclpy.spin(lift_node)
    except KeyboardInterrupt:
        print('Shutting down lift node...')
    finally:
        lift_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
