import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.opentrafficmap.device_tracker import OtmDeviceTracker, SourceType


def test_tracker_initial_state():
    t = OtmDeviceTracker("2844264451")
    assert t.unique_id == "otm_2844264451"
    assert t.name == "OTM Vehicle 2844264451"
    assert t.latitude is None
    assert t.longitude is None
    assert t.source_type == SourceType.GPS


def test_tracker_update():
    t = OtmDeviceTracker("2844264451")
    t.update_position(49.5071242, 8.5219273)
    assert t.latitude == 49.5071242
    assert t.longitude == 8.5219273
