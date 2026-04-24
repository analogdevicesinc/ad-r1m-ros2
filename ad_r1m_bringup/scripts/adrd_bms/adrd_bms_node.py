#!/usr/bin/env python3
"""
ADRD5161-01Z BMS Node

Subscribes to CANopen PDO data from the BMS and publishes ROS2 BatteryState messages.

CANopen Object Dictionary (CiA 419 profile):
- 0x6000: batteryStatus (8-bit) - 1=discharging, 0=charging
- 0x6001: chargerStatus (8-bit) - 0=?, 1=charging, 2=fault, 3=off, 4=full
- 0x6010: temperature (16-bit signed, °C)
- 0x6052: ahReturnedDuringLastCharge (16-bit, mAh)
- 0x6060: batteryVoltage (32-bit, mV)
- 0x6070: chargeCurrentRequested (16-bit)
- 0x6080: chargerStateOfCharge (8-bit, %)
- 0x6081: batteryStateOfCharge (8-bit, %)

Manufacturer-specific:
- 0x2060: batteryCellVoltages (array sub 1-4, 16-bit each, mV)
- 0x2071: current (32-bit signed, µA)
"""

import rclpy
from rclpy.node import Node
from canopen_interfaces.msg import COData
from canopen_interfaces.srv import CORead
from sensor_msgs.msg import BatteryState

NCELLS = 4


class AdrdBmsNode(Node):
    def __init__(self):
        super().__init__('adrd_bms')

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
        self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN
        self.battery_state.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_UNKNOWN
        self.battery_state.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LIPO
        self.battery_state.present = False
        self.battery_state.cell_voltage = [nan] * NCELLS
        self.battery_state.cell_temperature = [nan] * NCELLS
        self.battery_state.location = 'ADRD5161'
        self.battery_state.serial_number = ''

        self._battery_status = 0
        self._charger_status = 0

        self.send_timer = self.create_timer(1e-3, self.transmit)
        self.send_timer.cancel()

    def rpdo_cb(self, codata):
        self.on_codata(codata)

    def transmit(self):
        self.send_timer.cancel()
        self.battery_state.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(self.battery_state)

    def _update_power_supply_status(self):
        """Update power_supply_status based on battery and charger status."""
        if self._charger_status == 1:
            self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        elif self._charger_status == 4:
            self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_FULL
        elif self._battery_status == 1:
            self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        elif self._charger_status == 3:
            self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        else:
            self.battery_state.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN

    def on_codata(self, codata: COData):
        """Update internal battery state based on incoming CANopen data."""
        self.battery_state.present = True

        match (codata.index, codata.subindex):
            case (0x6000, 0):  # Battery status (1=discharging)
                self._battery_status = codata.data
                self._update_power_supply_status()
                self.get_logger().debug(
                    f'Battery status: {"discharging" if codata.data == 1 else "charging"}')

            case (0x6001, 0):  # Charger status
                self._charger_status = codata.data
                self._update_power_supply_status()
                status_str = {0: '?', 1: 'charging', 2: 'fault', 3: 'off', 4: 'full'}
                self.get_logger().debug(f'Charger status: {status_str.get(codata.data, "unknown")}')

            case (0x6010, 0):  # Temperature (°C, signed 16-bit)
                temp = codata.data if codata.data < 0x8000 else codata.data - 0x10000
                self.battery_state.temperature = float(temp)
                self.get_logger().debug(f'Temperature: {temp} °C')

            case (0x6052, 0):  # Ah returned during last charge (mAh)
                self.battery_state.capacity = codata.data / 1000.0
                self.get_logger().debug(f'Capacity: {codata.data} mAh')

            case (0x6060, 0):  # Battery voltage (mV)
                self.battery_state.voltage = codata.data / 1000.0
                self.get_logger().info(f'Voltage: {self.battery_state.voltage:.2f} V')

            case (0x6070, 0):  # Charge current requested (ignored for actual current)
                pass

            case (0x6080, 0):  # Charger state of charge (%)
                self.battery_state.percentage = codata.data / 100.0
                self.get_logger().debug(f'SOC (charger): {codata.data}%')

            case (0x6081, 0):  # Battery state of charge (%)
                self.battery_state.percentage = codata.data / 100.0
                self.get_logger().info(f'SOC: {codata.data}%')

            case (0x2060, subindex) if 1 <= subindex <= 4:  # Cell voltages (mV)
                cell_idx = subindex - 1
                self.battery_state.cell_voltage[cell_idx] = codata.data / 1000.0
                self.get_logger().debug(
                    f'Cell {subindex}: {codata.data} mV')

            case (0x2071, 0):  # Actual current (µA, signed 32-bit)
                current = codata.data if codata.data < 0x80000000 else codata.data - 0x100000000
                self.battery_state.current = current / 1_000_000.0
                self.get_logger().debug(f'Current: {current/1000:.1f} mA')

        self.send_timer.reset()


def main(args=None):
    rclpy.init(args=args)
    node = AdrdBmsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
