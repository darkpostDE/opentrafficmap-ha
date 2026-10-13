from __future__ import annotations
import json
import ssl
import logging
import paho.mqtt.client as mqtt
from .const import CONF_VEHICLE_TOPIC, CONF_STATS_TOPIC, CONF_ENABLED_SENSORS, ALL_CAM_SENSORS, DEFAULT_ENABLED_SENSORS
from .sensor import OtmVehicleSensor, OtmNodeSensor
from .device_tracker import OtmDeviceTracker

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.core import HomeAssistant
except ImportError:
    HomeAssistant = object


def parse_vehicle_msg(payload: str) -> dict | None:
    try:
        data = json.loads(payload)
        its = data["decoded"]["layers"]["its"]
        alt_raw = int(its["its_its_altitudeValue"])
        # 32760 = unavailable in ETSI ITS
        altitude = None if alt_raw == 32760 else round(alt_raw / 100.0, 1)
        return {
            "station_id": str(its["its_its_stationId"]),
            "lat": int(its["its_its_latitude"]) / 1e7,
            "lon": int(its["its_its_longitude"]) / 1e7,
            "speed": int(its["its_its_speedValue"]) * 0.01 * 3.6,
            "heading": int(its["its_its_headingValue"]) / 10.0,
            "station_type": str(its["its_its_stationType"]),
            "altitude": altitude,
            "yaw_rate": round(int(its["its_its_yawRateValue"]) / 100.0, 2),
            "drive_direction": "forward" if str(its.get("its_cam_driveDirection", "0")) == "0" else "backward",
            "brake_engaged": bool(its.get("its_its_AccelerationControl_brakePedalEngaged", False)),
            "gas_engaged": bool(its.get("its_its_AccelerationControl_gasPedalEngaged", False)),
            "vehicle_length": round(int(its["its_its_vehicleLengthValue"]) / 10.0, 1),
            "vehicle_width": round(int(its["its_cam_vehicleWidth"]) / 10.0, 1),
        }
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return None


def parse_stats_msg(payload: str) -> dict | None:
    try:
        data = json.loads(payload)
        return {"temp": data["temp"], "rbt": data["rbt"]}
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return None


class OtmMqttClient:
    def __init__(self, hass, data: dict, options: dict, add_vehicle_cb, add_stats_cb) -> None:
        self._hass = hass
        self._data = data
        self._add_vehicle_cb = add_vehicle_cb
        self._add_stats_cb = add_stats_cb
        self._client: mqtt.Client | None = None
        self._known_stations: set[str] = set()
        self._node_sensors: dict[str, OtmNodeSensor] = {}
        self._vehicle_entities: dict[str, dict] = {}
        parts = data[CONF_STATS_TOPIC].split("/")
        self._node_id = parts[1] if len(parts) >= 2 else "node"
        raw = options.get(CONF_ENABLED_SENSORS)
        if isinstance(raw, dict):
            self._enabled = [s for s in ALL_CAM_SENSORS if raw.get(s, False)]
        elif isinstance(raw, list):
            self._enabled = raw
        else:
            self._enabled = DEFAULT_ENABLED_SENSORS

    def start(self) -> None:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            client = mqtt.Client()
        client.username_pw_set(self._data["username"], self._data["password"])
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect_async(self._data["host"], self._data["port"], keepalive=60)
        client.loop_start()
        self._client = client

    def stop(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc != 0:
            _LOGGER.error("MQTT connect failed rc=%s", rc)
            return
        client.subscribe(self._data[CONF_VEHICLE_TOPIC])
        client.subscribe(self._data[CONF_STATS_TOPIC])
        _LOGGER.debug("MQTT connected, subscribed to topics")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore")
        if topic == self._data[CONF_VEHICLE_TOPIC]:
            self._handle_vehicle(payload)
        elif topic == self._data[CONF_STATS_TOPIC]:
            self._handle_stats(payload)

    def _handle_vehicle(self, payload: str) -> None:
        parsed = parse_vehicle_msg(payload)
        if not parsed:
            return
        sid = parsed["station_id"]
        if sid not in self._known_stations:
            self._known_stations.add(sid)
            tracker = OtmDeviceTracker(sid)
            entities = {"tracker": tracker}
            for s in self._enabled:
                entities[s] = OtmVehicleSensor(sid, s)
            self._vehicle_entities[sid] = entities
            self._hass.add_job(self._add_vehicle_cb, list(entities.values()))
        ents = self._vehicle_entities[sid]
        ents["tracker"].update_position(parsed["lat"], parsed["lon"])
        for s in self._enabled:
            if s in parsed:
                ents[s].update_value(parsed[s] if s not in ("speed",) else round(parsed[s], 1))

    def _handle_stats(self, payload: str) -> None:
        parsed = parse_stats_msg(payload)
        if not parsed:
            return
        if not self._node_sensors:
            temp_s = OtmNodeSensor(self._node_id, "temp")
            rbt_s = OtmNodeSensor(self._node_id, "rbt")
            self._node_sensors = {"temp": temp_s, "rbt": rbt_s}
            self._hass.add_job(self._add_stats_cb, [temp_s, rbt_s])
        self._node_sensors["temp"].update_value(parsed["temp"])
        self._node_sensors["rbt"].update_value(parsed["rbt"])
