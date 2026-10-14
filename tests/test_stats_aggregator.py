import json
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.opentrafficmap.stats_aggregator import OtmStatsAggregator

VEHICLE = {
    "station_id": "111",
    "speed": 50.0,
    "station_type": "5",
    "lat": 49.5,
    "lon": 8.7,
    "emergency_brake_engaged": False,
    "collision_warning_engaged": False,
}


def make_agg(tmpdir):
    return OtmStatsAggregator("node1411", tmpdir)


def test_new_vehicle_event():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        events = agg.update(VEHICLE)
        assert any(e[0] == "otm_new_vehicle" for e in events)
        assert agg.vehicles_total == 1


def test_same_vehicle_no_new_event():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        agg.update(VEHICLE)
        events = agg.update(VEHICLE)
        assert not any(e[0] == "otm_new_vehicle" for e in events)
        assert agg.vehicles_total == 1


def test_speed_avg():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        agg.update({**VEHICLE, "speed": 40.0})
        agg.update({**VEHICLE, "station_id": "222", "speed": 60.0})
        assert agg.speed_avg == 50.0


def test_speed_max_record_event():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        events = agg.update({**VEHICLE, "speed": 80.0})
        assert any(e[0] == "otm_speed_record" for e in events)
        assert agg.speed_max == 80.0
        events2 = agg.update({**VEHICLE, "station_id": "222", "speed": 50.0})
        assert not any(e[0] == "otm_speed_record" for e in events2)


def test_emergency_brake_event():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        events = agg.update({**VEHICLE, "emergency_brake_engaged": True})
        assert any(e[0] == "otm_emergency_brake" for e in events)
        assert agg.emergency_brakes == 1


def test_collision_warning_event():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        events = agg.update({**VEHICLE, "collision_warning_engaged": True})
        assert any(e[0] == "otm_collision_warning" for e in events)
        assert agg.collision_warnings == 1


def test_station_type_counts():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        agg.update({**VEHICLE, "station_id": "111", "station_type": "5"})
        agg.update({**VEHICLE, "station_id": "222", "station_type": "8"})
        counts = json.loads(agg.station_type_counts)
        assert counts["5"] == 1
        assert counts["8"] == 1


def test_persistence():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        agg.update({**VEHICLE, "speed": 90.0})
        # reload from disk
        agg2 = make_agg(d)
        assert agg2.speed_max == 90.0
        assert agg2.vehicles_total == 1


def test_debug_attributes():
    with tempfile.TemporaryDirectory() as d:
        agg = make_agg(d)
        agg.update(VEHICLE)
        attrs = agg.debug_attributes
        assert attrs["last_vehicle"]["station_id"] == "111"
        assert attrs["known_stations"] == 1
        assert attrs["last_seen"] is not None
