from __future__ import annotations
try:
    from homeassistant.components.sensor import SensorEntity, SensorStateClass
    from homeassistant.const import UnitOfTemperature, UnitOfTime
except ImportError:
    SensorEntity = object
    class SensorStateClass:
        MEASUREMENT = "measurement"
    class UnitOfTemperature:
        CELSIUS = "°C"
    class UnitOfTime:
        HOURS = "h"

from .const import DOMAIN

_VEHICLE_SENSOR_META = {
    "speed":                    ("Speed",                    "km/h",  True),
    "heading":                  ("Heading",                  "°",     True),
    "station_type":             ("Station Type",             None,    False),
    "altitude":                 ("Altitude",                 "m",     True),
    "yaw_rate":                 ("Yaw Rate",                 "°/s",   True),
    "drive_direction":          ("Drive Direction",          None,    False),
    "brake_engaged":            ("Brake Engaged",            None,    False),
    "gas_engaged":              ("Gas Engaged",              None,    False),
    "emergency_brake_engaged":  ("Emergency Brake",          None,    False),
    "collision_warning_engaged":("Collision Warning",        None,    False),
    "acc_engaged":              ("ACC Engaged",              None,    False),
    "cruise_control_engaged":   ("Cruise Control",          None,    False),
    "speed_limiter_engaged":    ("Speed Limiter",            None,    False),
    "vehicle_length":           ("Vehicle Length",           "m",     True),
    "vehicle_width":            ("Vehicle Width",            "m",     True),
}

_NODE_SENSOR_META = {
    "temp":                ("Temperature",       UnitOfTemperature.CELSIUS, True),
    "rbt":                 ("Uptime",            UnitOfTime.HOURS,          True),
    "vehicles_total":      ("Vehicles Total",    None,                      True),
    "speed_avg":           ("Avg Speed",         "km/h",                    True),
    "speed_max":           ("Max Speed",         "km/h",                    True),
    "emergency_brakes":    ("Emergency Brakes",  None,                      True),
    "collision_warnings":  ("Collision Warnings",None,                      True),
    "station_type_counts": ("Station Types",     None,                      False),
    "debug":               ("Debug",             None,                      False),
}


class OtmAggSensor(SensorEntity):
    """Aggregation sensor with optional extra_state_attributes."""
    _attr_should_poll = False

    def __init__(self, node_id: str, sensor_type: str) -> None:
        label, unit, numeric = _NODE_SENSOR_META[sensor_type]
        self._attr_unique_id = f"otm_{node_id}_{sensor_type}"
        self._attr_name = f"OTM {node_id} {label}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = None
        self._attr_state_class = SensorStateClass.MEASUREMENT if numeric else None
        self._extra_attrs: dict = {}

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        return self._extra_attrs or None

    def update_value(self, value, attrs: dict | None = None) -> None:
        self._attr_native_value = value
        if attrs is not None:
            self._extra_attrs = attrs
        if hasattr(self, 'hass') and self.hass:
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


class OtmVehicleSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, station_id: str, sensor_type: str) -> None:
        label, unit, numeric = _VEHICLE_SENSOR_META[sensor_type]
        self._attr_unique_id = f"otm_{station_id}_{sensor_type}"
        self._attr_name = f"OTM {station_id} {label}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = None
        self._attr_state_class = SensorStateClass.MEASUREMENT if numeric else None
        self._station_id = station_id
        self._sensor_type = sensor_type

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self):
        return self._attr_native_value

    def update_value(self, value) -> None:
        self._attr_native_value = value
        if hasattr(self, 'hass') and self.hass:
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


class OtmNodeSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, node_id: str, sensor_type: str) -> None:
        label, unit, numeric = _NODE_SENSOR_META[sensor_type]
        self._attr_unique_id = f"otm_{node_id}_{sensor_type}"
        self._attr_name = f"OTM {node_id} {label}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = None
        self._attr_state_class = SensorStateClass.MEASUREMENT if numeric else None
        self._node_id = node_id
        self._sensor_type = sensor_type

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self):
        return self._attr_native_value

    def update_value(self, value) -> None:
        self._attr_native_value = value
        if hasattr(self, 'hass') and self.hass:
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
    ) -> None:
        hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
        # both node sensors and aggregation sensors use the same platform callback
        hass.data[DOMAIN][entry.entry_id]["add_stats"] = async_add_entities
except ImportError:
    pass
