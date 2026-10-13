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
