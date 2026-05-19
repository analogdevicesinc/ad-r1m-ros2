#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from canopen_interfaces.msg import COData
from canopen_interfaces.srv import CORead
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Header

NCELLS = 3


class AdrdBmsNode(Node):
    def __init__(self):
        super().__init__('adrd_bms')

        # rclpy.Parameter.Type.STRING)
        self.declare_parameter('canopen_proxy_node', 'bms_canopen')

        canopen_proxy_node = str(
            self.get_parameter('canopen_proxy_node').value)

        self.sdo_read_cli = self.create_client(
            CORead, f'{canopen_proxy_node}/sdo_read')
        self.rpdo_sub = self.create_subscription(
            COData, f'{canopen_proxy_node}/rpdo', self.rpdo_cb, 5)

        self.publisher = self.create_publisher(
            BatteryState, 'battery_state', 5)

        self.battery_state = BatteryState()
        nan = float('nan')
        self.battery_state.voltage = nan
        self.battery_state.temperature = nan
        self.battery_state.current = nan
        self.battery_state.charge = nan
        self.battery_state.capacity = nan
        self.battery_state.design_capacity = nan
        self.battery_state.percentage = nan
        self.battery_state.power_supply_status = 0  # unknown
        self.battery_state.power_supply_health = 0  # unknown
        self.battery_state.power_supply_technology = 3  # LIPO
        self.battery_state.present = False
        self.battery_state.cell_voltage = [nan] * NCELLS
        self.battery_state.cell_temperature = [nan] * NCELLS
        self.battery_state.location = 'BMS'
        self.battery_state.serial_number = '???'

        # Wait 1ms before transmitting battery state to allow
        # multiple updates to be grouped before a send
        self.send_timer = self.create_timer(1e-3, self.transmit)
        self.send_timer.cancel()

    def rpdo_cb(self, codata):
        self.on_codata(codata)

    def canopen_read(self, index, subindex):
        req = self.sdo_read_client.Request()
        req.index = index
        req.subindex = subindex
        self.sdo_read_client.call(req)

    def read_constant_specs(self):
        """
        Update internal battery state fields which are assumed to be constant.

        Assumes BMS is alive.
        """
        pass

    def transmit(self):
        self.send_timer.cancel()  # One-shot

    def on_codata(self, codata: COData):
        """
        Update internal battery state based on incoming CANopen data.

        Schedule an event-based transmission.
        """
        match (codata.index, codata.subindex):
            case (0x6000, 0):  # Battery status
                self.battery_ready = codata.data & 1
                print(f'battery_ready = {self.battery_ready}')

            case (0x6001, 0):  # Charger status
                self.charger_ready = codata.data & 1
                print(f'charger_ready = {self.charger_ready}')

            case (0x6010, 0):  # Temperature
                self.battery_state.temperature = codata.data * 0.125
                print(f'temperature = {self.battery_state.temperature} C')

            case (0x6052, 0):  # Ah returned during last charge
                self.battery_state.capacity = codata.data * 0.125
                print(f'capacity = {self.battery_state.capacity} Ah')

            case (0x6060, 0):  # Battery voltage
                self.battery_state.voltage = codata.data * 1 / 1024.0
                print(f'BATT = {self.battery_state.voltage:.1f} V')

            case (0x6070, 0):  # Charge current requested
                self.battery_state.current = codata.data * 1 / 16.0
                print(f'CURR = {int(self.battery_state.current * 1000)} mA')

            case (0x6080, 0):  # Charger state of charge
                self.battery_state.percentage = codata.data / 100.0
                print(
                    f'SOC (charger) = {int(self.battery_state.percentage * 100)} %')

            case (0x6081, 0):  # Battery state of charge
                self.battery_state.percentage = codata.data / 100.0
                print(
                    f'SOC (batt) = {int(self.battery_state.percentage * 100)} %')

        # Update timestamp
        self.battery_state.header = Header()

        self.send_timer.reset()  # Schedule transmit in 1ms, if not prolonged


def main(args=None):
    rclpy.init(args=args)

    node = AdrdBmsNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
