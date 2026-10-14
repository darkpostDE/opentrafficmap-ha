import pytest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.opentrafficmap.mqtt_client import parse_vehicle_msg, parse_stats_msg

SAMPLE_VEHICLE_JSON = {
    "decoded": {
        "layers": {
            "its": {
                "its_its_latitude": "495071242",
                "its_its_longitude": "85219273",
                "its_its_speedValue": "457",
                "its_its_headingValue": "444",
                "its_its_stationType": "5",
                "its_its_stationId": "2844264451",
                "its_its_altitudeValue": "14560",
                "its_its_yawRateValue": "-1555",
                "its_cam_driveDirection": "0",
                "its_its_AccelerationControl_brakePedalEngaged": False,
                "its_its_AccelerationControl_gasPedalEngaged": True,
                "its_its_AccelerationControl_emergencyBrakeEngaged": False,
                "its_its_AccelerationControl_collisionWarningEngaged": True,
                "its_its_AccelerationControl_accEngaged": False,
                "its_its_AccelerationControl_cruiseControlEngaged": True,
                "its_its_AccelerationControl_speedLimiterEngaged": False,
                "its_its_vehicleLengthValue": "46",
                "its_cam_vehicleWidth": "18",
            }
        }
    }
}

SAMPLE_STATS_JSON = {"temp": 29.5, "rbt": 8448}


def test_parse_vehicle_msg():
    result = parse_vehicle_msg(json.dumps(SAMPLE_VEHICLE_JSON))
    assert result["station_id"] == "2844264451"
    assert abs(result["lat"] - 49.5071242) < 0.0000001
    assert abs(result["lon"] - 8.5219273) < 0.0000001
    assert abs(result["speed"] - 16.452) < 0.01
    assert abs(result["heading"] - 44.4) < 0.01
    assert result["station_type"] == "Passenger Car"
    assert result["altitude"] == 145.6
    assert result["yaw_rate"] == -15.55
    assert result["drive_direction"] == "forward"
    assert result["brake_engaged"] is False
    assert result["gas_engaged"] is True
    assert result["emergency_brake_engaged"] is False
    assert result["collision_warning_engaged"] is True
    assert result["acc_engaged"] is False
    assert result["cruise_control_engaged"] is True
    assert result["speed_limiter_engaged"] is False
    assert result["vehicle_length"] == 4.6
    assert result["vehicle_width"] == 1.8


def test_parse_vehicle_msg_invalid():
    assert parse_vehicle_msg("not json") is None
    assert parse_vehicle_msg("{}") is None


def test_parse_stats_msg():
    result = parse_stats_msg(json.dumps(SAMPLE_STATS_JSON))
    assert result["temp"] == 29.5
    assert result["rbt"] == 8448


def test_parse_stats_msg_invalid():
    assert parse_stats_msg("bad") is None


def test_parse_vehicle_msg_altitude_unavailable():
    sample = json.loads(json.dumps(SAMPLE_VEHICLE_JSON))
    sample["decoded"]["layers"]["its"]["its_its_altitudeValue"] = "32760"
    result = parse_vehicle_msg(json.dumps(sample))
    assert result["altitude"] is None


def test_parse_vehicle_msg_backward():
    sample = json.loads(json.dumps(SAMPLE_VEHICLE_JSON))
    sample["decoded"]["layers"]["its"]["its_cam_driveDirection"] = "1"
    result = parse_vehicle_msg(json.dumps(sample))
    assert result["drive_direction"] == "backward"
