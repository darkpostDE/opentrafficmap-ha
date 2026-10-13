from __future__ import annotations
try:
    from homeassistant.components.device_tracker import SourceType, TrackerEntity
except ImportError:
    TrackerEntity = object
    class SourceType:
        GPS = "gps"

from .const import DOMAIN


class OtmDeviceTracker(TrackerEntity):
    _attr_should_poll = False

    def __init__(self, station_id: str) -> None:
        self._attr_unique_id = f"otm_{station_id}"
        self._attr_name = f"OTM Vehicle {station_id}"
        self._lat: float | None = None
        self._lon: float | None = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return self._lat

    @property
    def longitude(self) -> float | None:
        return self._lon

    def update_position(self, lat: float, lon: float) -> None:
        self._lat = lat
        self._lon = lon
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
        hass.data[DOMAIN][entry.entry_id]["add_vehicle"] = async_add_entities
except ImportError:
    pass
