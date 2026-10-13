import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.opentrafficmap.sensor import OtmVehicleSensor, OtmNodeSensor


def test_vehicle_sensor_speed_initial():
    s = OtmVehicleSensor("2844264451", "speed")
    assert s.unique_id == "otm_2844264451_speed"
    assert s.name == "OTM 2844264451 Speed"
    assert s.native_unit_of_measurement == "km/h"
    assert s.native_value is None


def test_vehicle_sensor_update():
    s = OtmVehicleSensor("2844264451", "speed")
    s.update_value(16.5)
    assert s.native_value == 16.5


def test_vehicle_sensor_heading():
    s = OtmVehicleSensor("2844264451", "heading")
    assert s.unique_id == "otm_2844264451_heading"
    assert s.native_unit_of_measurement == "°"


def test_vehicle_sensor_station_type():
    s = OtmVehicleSensor("2844264451", "station_type")
    assert s.native_unit_of_measurement is None


def test_vehicle_sensor_altitude():
    s = OtmVehicleSensor("2844264451", "altitude")
    assert s.unique_id == "otm_2844264451_altitude"
    assert s.native_unit_of_measurement == "m"
    s.update_value(145.6)
    assert s.native_value == 145.6


def test_vehicle_sensor_altitude_unavailable():
    s = OtmVehicleSensor("2844264451", "altitude")
    s.update_value(None)
    assert s.native_value is None


def test_vehicle_sensor_yaw_rate():
    s = OtmVehicleSensor("2844264451", "yaw_rate")
    assert s.native_unit_of_measurement == "°/s"
    s.update_value(-15.55)
    assert s.native_value == -15.55


def test_vehicle_sensor_drive_direction():
    s = OtmVehicleSensor("2844264451", "drive_direction")
    assert s.native_unit_of_measurement is None
    s.update_value("forward")
    assert s.native_value == "forward"
    s.update_value("backward")
    assert s.native_value == "backward"


def test_vehicle_sensor_brake_engaged():
    s = OtmVehicleSensor("2844264451", "brake_engaged")
    assert s.native_unit_of_measurement is None
    s.update_value(False)
    assert s.native_value is False


def test_vehicle_sensor_gas_engaged():
    s = OtmVehicleSensor("2844264451", "gas_engaged")
    s.update_value(True)
    assert s.native_value is True


def test_vehicle_sensor_vehicle_length():
    s = OtmVehicleSensor("2844264451", "vehicle_length")
    assert s.native_unit_of_measurement == "m"
    s.update_value(4.6)
    assert s.native_value == 4.6


def test_vehicle_sensor_vehicle_width():
    s = OtmVehicleSensor("2844264451", "vehicle_width")
    assert s.native_unit_of_measurement == "m"
    s.update_value(1.8)
    assert s.native_value == 1.8


def test_node_sensor_temp():
    s = OtmNodeSensor("node1411", "temp")
    assert s.unique_id == "otm_node1411_temp"
    assert s.name == "OTM node1411 Temperature"
    assert s.native_unit_of_measurement == "°C"


def test_node_sensor_uptime():
    s = OtmNodeSensor("node1411", "rbt")
    assert s.unique_id == "otm_node1411_rbt"
    assert s.name == "OTM node1411 Uptime"
    assert s.native_unit_of_measurement == "s"
