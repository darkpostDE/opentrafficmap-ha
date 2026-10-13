from __future__ import annotations
try:
    from homeassistant.components.sensor import SensorEntity, SensorStateClass
    from homeassistant.const import UnitOfTemperature
except ImportError:
    SensorEntity = object
    class SensorStateClass:
        MEASUREMENT = "measurement"
    class UnitOfTemperature:
        CELSIUS = "°C"

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
    "temp": ("Temperature", UnitOfTemperature.CELSIUS, True),
    "rbt":  ("Uptime",      "s",                       True),
}


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
            self.async_write_ha_state()


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
            self.async_write_ha_state()


try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
    ) -> None:
        hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
        hass.data[DOMAIN][entry.entry_id]["add_stats"] = async_add_entities
except ImportError:
    pass
