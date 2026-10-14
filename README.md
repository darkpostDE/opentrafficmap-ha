# OpenTrafficMap — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

Integrates live V2X (Vehicle-to-Everything) traffic data from [opentrafficmap.org](https://opentrafficmap.org) into Home Assistant. Vehicles passing your registered roadside node broadcast ETSI ITS CAM messages — opentrafficmap.org decodes them and forwards the data via MQTT. This integration subscribes to that feed, creates entities for each detected vehicle, and maintains persistent traffic statistics.

## What It Does

- Connects to the opentrafficmap.org MQTT broker (TLS, port 8883) using your node credentials
- Receives decoded CAM messages from vehicles passing your node
- Auto-creates a **Device Tracker** (GPS position on map) per vehicle
- Auto-creates **Sensors** per vehicle: speed, heading, station type, altitude, yaw rate, drive direction, brake/gas/emergency brake/collision warning/ACC/cruise control/speed limiter state, vehicle dimensions
- Creates **Node sensors** for your node's telemetry: temperature and uptime
- Builds **Traffic statistics** (total vehicles seen, average/max speed, safety event counts, station type distribution) stored persistently across restarts
- Fires **HA events** for automations: new vehicle detected, new speed record, emergency brake, collision warning
- Configurable sensor selection and vehicle retention period via UI
- Auto-reconnects to MQTT broker on connection loss (5–60s backoff)

## Requirements

- Home Assistant 2024.1 or newer
- An account on [opentrafficmap.org](https://opentrafficmap.org) with a registered node
- Your node credentials (Node ID, MQTT password)

---

## Installation

### Option A: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add: `https://github.com/darkpostDE/opentrafficmap-ha` — Category: **Integration**
4. Click **Download** on the OpenTrafficMap integration
5. Restart Home Assistant

### Option B: Manual

1. Download or clone this repository
2. Copy the `custom_components/opentrafficmap/` folder into your HA config directory:

```bash
cp -r custom_components/opentrafficmap /config/custom_components/
```

3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **OpenTrafficMap**
3. Fill in your node credentials:

| Field | Example |
|-------|---------|
| Host | `cits1.opentrafficmap.org` |
| Port | `8883` |
| Username | `node1411` |
| Password | `your-mqtt-password` |
| Vehicle Topic | `its/node1411/packet/json` |
| Stats Topic | `its/node1411/stats` |

Replace `node1411` with your actual node ID.

4. Click **Submit** — the integration validates the connection before saving

### Sensor Selection & Retention

After setup, click **Configure** on the integration to choose which CAM fields to expose as sensors and how long vehicles are kept:

- Speed, Heading, Station Type *(default)*
- Altitude, Yaw Rate, Drive Direction
- Brake Engaged, Gas Engaged
- Emergency Brake Engaged, Collision Warning Engaged
- ACC Engaged, Cruise Control Engaged, Speed Limiter Engaged
- Vehicle Length, Vehicle Width

**Vehicle TTL** (default: 300 s) — vehicles with no message for this duration are removed from HA. Set to `0` to never remove. Historical statistics are kept regardless.

---

## Entities

### Per Vehicle (auto-created when a vehicle is first detected)

| Entity | Unit | Description |
|--------|------|-------------|
| `device_tracker.otm_<stationId>` | — | GPS position (visible on Map card) |
| `sensor.otm_<stationId>_speed` | km/h | Current speed |
| `sensor.otm_<stationId>_heading` | ° | Direction of travel |
| `sensor.otm_<stationId>_station_type` | — | Vehicle type (5 = passenger car) |
| `sensor.otm_<stationId>_altitude` | m | Altitude (None if unavailable) |
| `sensor.otm_<stationId>_yaw_rate` | °/s | Rotation rate |
| `sensor.otm_<stationId>_drive_direction` | — | `forward` or `backward` |
| `sensor.otm_<stationId>_brake_engaged` | — | Brake pedal state |
| `sensor.otm_<stationId>_gas_engaged` | — | Gas pedal state |
| `sensor.otm_<stationId>_emergency_brake_engaged` | — | Emergency brake active |
| `sensor.otm_<stationId>_collision_warning_engaged` | — | Collision warning active |
| `sensor.otm_<stationId>_acc_engaged` | — | Adaptive cruise control active |
| `sensor.otm_<stationId>_cruise_control_engaged` | — | Cruise control active |
| `sensor.otm_<stationId>_speed_limiter_engaged` | — | Speed limiter active |
| `sensor.otm_<stationId>_vehicle_length` | m | Vehicle length |
| `sensor.otm_<stationId>_vehicle_width` | m | Vehicle width |

### Node Device

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.otm_<nodeId>_temp` | °C | Node temperature |
| `sensor.otm_<nodeId>_rbt` | h | Node uptime in hours |

### Traffic Statistics (persistent, auto-created on first vehicle)

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.otm_<nodeId>_vehicles_total` | — | All-time unique vehicle count |
| `sensor.otm_<nodeId>_speed_avg` | km/h | Average speed across all readings |
| `sensor.otm_<nodeId>_speed_max` | km/h | All-time maximum speed observed |
| `sensor.otm_<nodeId>_emergency_brakes` | — | Emergency brake event count |
| `sensor.otm_<nodeId>_collision_warnings` | — | Collision warning event count |
| `sensor.otm_<nodeId>_station_type_counts` | — | JSON map of vehicle types seen |
| `sensor.otm_<nodeId>_debug` | — | Last vehicle + known station count (attributes) |

Statistics are stored in `/config/custom_components/opentrafficmap/stats_<nodeId>.json` and survive restarts.

---

## HA Events

The integration fires HA events that can be used in automations. Go to **Developer Tools → Events** to inspect them.

| Event | Fires when | Key data fields |
|-------|-----------|-----------------|
| `otm_new_vehicle` | A new station ID is seen for the first time | `station_id`, `speed`, `station_type`, `lat`, `lon` |
| `otm_speed_record` | A new all-time speed maximum is set | `station_id`, `speed`, `previous_max` |
| `otm_emergency_brake` | A vehicle reports emergency brake engaged | `station_id`, `speed`, `lat`, `lon` |
| `otm_collision_warning` | A vehicle reports collision warning engaged | `station_id`, `speed`, `lat`, `lon` |

### Example Automations

**Notify when a new vehicle passes:**

```yaml
automation:
  - alias: "New vehicle detected"
    trigger:
      - platform: event
        event_type: otm_new_vehicle
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "New Vehicle"
          message: "Station {{ trigger.event.data.station_id }} at {{ trigger.event.data.speed | round(0) }} km/h"
```

**Alert on emergency brake nearby:**

```yaml
automation:
  - alias: "Emergency brake alert"
    trigger:
      - platform: event
        event_type: otm_emergency_brake
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Brake Detected"
          message: "Vehicle {{ trigger.event.data.station_id }} at {{ trigger.event.data.speed | round(0) }} km/h"
```

**Log new speed record:**

```yaml
automation:
  - alias: "Speed record"
    trigger:
      - platform: event
        event_type: otm_speed_record
    action:
      - service: logbook.log
        data:
          name: "Speed Record"
          message: "{{ trigger.event.data.speed }} km/h by {{ trigger.event.data.station_id }} (was {{ trigger.event.data.previous_max }} km/h)"
```

---

## Debug Logging

Add to your HA `configuration.yaml` to enable verbose logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.opentrafficmap: debug
```

Logs show MQTT connect/disconnect, every incoming message (topic + length), new vehicle detection, entity creation, TTL cleanup, fired events, and statistics updates. View in **Settings → System → Logs**.

---

## Map Card

Add a Map card to your dashboard and select `device_tracker.otm_*` entities to see vehicle positions in real time. Entities only appear after the first vehicle message is received.

---

## Long-Term Statistics

Numeric sensors (speed, heading, altitude, etc.) have `state_class: measurement` set so Home Assistant Recorder stores min/max/mean over time. Access via **Developer Tools → Statistics** or a **Statistics Graph Card**.

The aggregation sensors (`vehicles_total`, `speed_avg`, `speed_max`, etc.) also have `state_class: measurement` — add them to history graphs to see traffic trends.

---

## How It Works

Vehicles equipped with V2X hardware (ITS-G5 / IEEE 802.11p) broadcast ETSI ITS CAM (Cooperative Awareness Messages) at up to 10 Hz. The opentrafficmap.org roadside unit at your node receives and decodes these packets, then forwards them as JSON to the MQTT broker. This integration subscribes to your node's topic, parses the decoded data into Home Assistant entities, and maintains persistent statistics.

---

## License

MIT
