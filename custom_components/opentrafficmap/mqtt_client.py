from __future__ import annotations
import json
import ssl
import logging
import time
import paho.mqtt.client as mqtt
from .const import (
    CONF_VEHICLE_TOPIC, CONF_STATS_TOPIC, CONF_ENABLED_SENSORS, CONF_VEHICLE_TTL,
    ALL_CAM_SENSORS, ALL_AGG_SENSORS, DEFAULT_ENABLED_SENSORS, DEFAULT_VEHICLE_TTL,
)
from .sensor import OtmVehicleSensor, OtmNodeSensor, OtmAggSensor
from .device_tracker import OtmDeviceTracker
from .stats_aggregator import OtmStatsAggregator

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
            "emergency_brake_engaged": bool(its.get("its_its_AccelerationControl_emergencyBrakeEngaged", False)),
            "collision_warning_engaged": bool(its.get("its_its_AccelerationControl_collisionWarningEngaged", False)),
            "acc_engaged": bool(its.get("its_its_AccelerationControl_accEngaged", False)),
            "cruise_control_engaged": bool(its.get("its_its_AccelerationControl_cruiseControlEngaged", False)),
            "speed_limiter_engaged": bool(its.get("its_its_AccelerationControl_speedLimiterEngaged", False)),
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
    def __init__(self, hass, data: dict, options: dict, add_vehicle_cb, add_stats_cb, config_dir: str = "") -> None:
        self._hass = hass
        self._data = data
        self._add_vehicle_cb = add_vehicle_cb
        self._add_stats_cb = add_stats_cb
        self._config_dir = config_dir
        self._client: mqtt.Client | None = None
        self._known_stations: set[str] = set()
        self._node_sensors: dict[str, OtmNodeSensor] = {}
        self._agg_sensors: dict[str, OtmAggSensor] = {}
        self._vehicle_entities: dict[str, dict] = {}
        self._last_seen: dict[str, float] = {}
        parts = data[CONF_STATS_TOPIC].split("/")
        self._node_id = parts[1] if len(parts) >= 2 else "node"
        raw = options.get(CONF_ENABLED_SENSORS)
        if isinstance(raw, dict):
            self._enabled = [s for s in ALL_CAM_SENSORS if raw.get(s, False)]
        elif isinstance(raw, list):
            self._enabled = raw
        elif any(s in options for s in ALL_CAM_SENSORS):
            # flat storage from OptionsFlow
            self._enabled = [s for s in ALL_CAM_SENSORS if options.get(s, False)]
        else:
            self._enabled = DEFAULT_ENABLED_SENSORS
        self._ttl = int(options.get(CONF_VEHICLE_TTL, DEFAULT_VEHICLE_TTL))
        self._aggregator: OtmStatsAggregator | None = None
        if config_dir:
            self._aggregator = OtmStatsAggregator(self._node_id, config_dir)
        _LOGGER.debug("OtmMqttClient init: enabled=%s ttl=%ss aggregator=%s", self._enabled, self._ttl, bool(self._aggregator))

    def start(self) -> None:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            client = mqtt.Client()
        client.username_pw_set(self._data["username"], self._data["password"])
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=5, max_delay=60)
        client.connect_async(self._data["host"], self._data["port"], keepalive=60)
        client.loop_start()
        self._client = client
        _LOGGER.debug("MQTT client started, connecting to %s:%s", self._data["host"], self._data["port"])

    def stop(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            _LOGGER.debug("MQTT client stopped")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc != 0:
            _LOGGER.error("MQTT connect failed rc=%s", rc)
            return
        client.subscribe(self._data[CONF_VEHICLE_TOPIC])
        client.subscribe(self._data[CONF_STATS_TOPIC])
        _LOGGER.debug("MQTT connected, subscribed vehicle=%s stats=%s",
                      self._data[CONF_VEHICLE_TOPIC], self._data[CONF_STATS_TOPIC])

    def _on_disconnect(self, client, userdata, rc) -> None:
        if rc != 0:
            _LOGGER.warning("MQTT disconnected unexpectedly rc=%s, will auto-reconnect (5-60s backoff)", rc)
        else:
            _LOGGER.debug("MQTT disconnected cleanly")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore")
        _LOGGER.debug("MQTT message topic=%s len=%d", topic, len(payload))
        if topic == self._data[CONF_VEHICLE_TOPIC]:
            self._handle_vehicle(payload)
        elif topic == self._data[CONF_STATS_TOPIC]:
            self._handle_stats(payload)

    def _handle_vehicle(self, payload: str) -> None:
        parsed = parse_vehicle_msg(payload)
        if not parsed:
            _LOGGER.debug("Vehicle message parse failed")
            return
        sid = parsed["station_id"]
        now = time.monotonic()
        self._last_seen[sid] = now

        if sid not in self._known_stations:
            self._known_stations.add(sid)
            tracker = OtmDeviceTracker(sid)
            entities = {"tracker": tracker}
            for s in self._enabled:
                entities[s] = OtmVehicleSensor(sid, s)
            self._vehicle_entities[sid] = entities
            self._hass.add_job(self._add_vehicle_cb, list(entities.values()))
            _LOGGER.debug("New vehicle station_id=%s, created %d entities", sid, len(entities))

        ents = self._vehicle_entities[sid]
        ents["tracker"].update_position(parsed["lat"], parsed["lon"])
        for s in self._enabled:
            if s in parsed:
                val = round(parsed[s], 1) if s == "speed" else parsed[s]
                ents[s].update_value(val)

        if self._aggregator:
            events = self._aggregator.update(parsed)
            self._push_agg_sensors()
            for event_type, event_data in events:
                self._hass.loop.call_soon_threadsafe(
                    self._hass.bus.async_fire, event_type, event_data
                )
                _LOGGER.debug("Fired event %s data=%s", event_type, event_data)

        if self._ttl > 0:
            self._cleanup_stale(now)

    def _push_agg_sensors(self) -> None:
        if not self._aggregator:
            return
        agg = self._aggregator
        if not self._agg_sensors:
            sensors = {k: OtmAggSensor(self._node_id, k) for k in ALL_AGG_SENSORS}
            self._agg_sensors = sensors
            self._hass.add_job(self._add_stats_cb, list(sensors.values()))
            _LOGGER.debug("Aggregation sensors created for node_id=%s", self._node_id)
        s = self._agg_sensors
        s["vehicles_total"].update_value(agg.vehicles_total)
        s["speed_avg"].update_value(agg.speed_avg)
        s["speed_max"].update_value(agg.speed_max)
        s["emergency_brakes"].update_value(agg.emergency_brakes)
        s["collision_warnings"].update_value(agg.collision_warnings)
        s["station_type_counts"].update_value(agg.station_type_counts)
        s["debug"].update_value(len(agg.debug_attributes), agg.debug_attributes)

    def _cleanup_stale(self, now: float) -> None:
        stale = [sid for sid, ts in self._last_seen.items() if now - ts > self._ttl]
        for sid in stale:
            _LOGGER.debug("Vehicle station_id=%s stale after %ss, removing", sid, self._ttl)
            self._known_stations.discard(sid)
            self._vehicle_entities.pop(sid, None)
            self._last_seen.pop(sid, None)

    def _handle_stats(self, payload: str) -> None:
        parsed = parse_stats_msg(payload)
        if not parsed:
            _LOGGER.debug("Stats message parse failed")
            return
        if not self._node_sensors:
            temp_s = OtmNodeSensor(self._node_id, "temp")
            rbt_s = OtmNodeSensor(self._node_id, "rbt")
            self._node_sensors = {"temp": temp_s, "rbt": rbt_s}
            self._hass.add_job(self._add_stats_cb, [temp_s, rbt_s])
            _LOGGER.debug("Node sensors created for node_id=%s", self._node_id)
        self._node_sensors["temp"].update_value(parsed["temp"])
        self._node_sensors["rbt"].update_value(round(parsed["rbt"] / 3600, 2))
        _LOGGER.debug("Node stats updated temp=%s rbt=%s", parsed["temp"], parsed["rbt"])

