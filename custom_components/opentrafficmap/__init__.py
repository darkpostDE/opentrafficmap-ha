from __future__ import annotations
import logging
from .const import DOMAIN, DATA_MQTT_CLIENT
from .mqtt_client import OtmMqttClient

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
except ImportError:
    pass

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["device_tracker", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    _LOGGER.debug("async_setup_entry options=%s", dict(entry.options))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    client = OtmMqttClient(
        hass,
        dict(entry.data),
        dict(entry.options),
        hass.data[DOMAIN][entry.entry_id]["add_vehicle"],
        hass.data[DOMAIN][entry.entry_id]["add_stats"],
        hass.config.config_dir,
    )
    hass.data[DOMAIN][entry.entry_id][DATA_MQTT_CLIENT] = client
    await hass.async_add_executor_job(client.start)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = hass.data[DOMAIN][entry.entry_id].get(DATA_MQTT_CLIENT)
    if client:
        await hass.async_add_executor_job(client.stop)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
