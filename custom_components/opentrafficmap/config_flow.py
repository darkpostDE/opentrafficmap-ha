from __future__ import annotations
import asyncio
import ssl
import paho.mqtt.client as mqtt
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from .const import (
    DOMAIN, CONF_VEHICLE_TOPIC, CONF_STATS_TOPIC,
    CONF_ENABLED_SENSORS, CONF_VEHICLE_TTL,
    ALL_CAM_SENSORS, DEFAULT_ENABLED_SENSORS, DEFAULT_VEHICLE_TTL,
)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default="cits1.opentrafficmap.org"): str,
    vol.Required(CONF_PORT, default=8883): int,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_VEHICLE_TOPIC, default="its/node1411/packet/json"): str,
    vol.Required(CONF_STATS_TOPIC, default="its/node1411/stats"): str,
})

_SENSOR_LABELS = {
    "speed":                     "Speed (km/h)",
    "heading":                   "Heading (°)",
    "station_type":              "Station Type",
    "altitude":                  "Altitude (m)",
    "yaw_rate":                  "Yaw Rate (°/s)",
    "drive_direction":           "Drive Direction",
    "brake_engaged":             "Brake Engaged",
    "gas_engaged":               "Gas Engaged",
    "emergency_brake_engaged":   "Emergency Brake Engaged",
    "collision_warning_engaged": "Collision Warning Engaged",
    "acc_engaged":               "ACC Engaged",
    "cruise_control_engaged":    "Cruise Control Engaged",
    "speed_limiter_engaged":     "Speed Limiter Engaged",
    "vehicle_length":            "Vehicle Length (m)",
    "vehicle_width":             "Vehicle Width (m)",
}


async def validate_connection(host: str, port: int, username: str, password: str) -> bool:
    loop = asyncio.get_event_loop()
    connected = asyncio.Event()
    failed = asyncio.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            connected.set()
        else:
            failed.set()

    def _connect():
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            client = mqtt.Client()
        client.username_pw_set(username, password)
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        client.on_connect = on_connect
        try:
            client.connect(host, port, keepalive=10)
            client.loop_start()
            return client
        except Exception:
            failed.set()
            return None

    try:
        client = await loop.run_in_executor(None, _connect)
        done, _ = await asyncio.wait(
            [loop.create_task(connected.wait()), loop.create_task(failed.wait())],
            timeout=10,
        )
        if client:
            client.loop_stop()
            client.disconnect()
        return connected.is_set()
    except Exception:
        return False


class OpenTrafficMapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            ok = await validate_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if ok:
                return self.async_create_entry(
                    title=f"OTM {user_input[CONF_HOST]}",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OpenTrafficMapOptionsFlow(config_entry)


class OpenTrafficMapOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        raw = self._config_entry.options.get(CONF_ENABLED_SENSORS, DEFAULT_ENABLED_SENSORS)
        if isinstance(raw, dict):
            enabled = {s for s, v in raw.items() if v}
        else:
            enabled = set(raw)

        schema = vol.Schema({
            vol.Optional(sensor, default=(sensor in enabled)): bool
            for sensor in ALL_CAM_SENSORS
        } | {
            vol.Optional(CONF_VEHICLE_TTL, default=int(self._config_entry.options.get(CONF_VEHICLE_TTL, DEFAULT_VEHICLE_TTL))): int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                s: _SENSOR_LABELS[s] for s in ALL_CAM_SENSORS
            },
        )
