# OpenTrafficMap — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

Integrates live V2X (Vehicle-to-Everything) traffic data from [opentrafficmap.org](https://opentrafficmap.org) into Home Assistant. Vehicles passing your registered roadside node broadcast ETSI ITS CAM messages — opentrafficmap.org decodes them and forwards the data via MQTT. This integration subscribes to that feed and automatically creates entities for each vehicle detected.

## What It Does

- Connects to the opentrafficmap.org MQTT broker (TLS, port 8883) using your node credentials
- Receives decoded CAM messages from vehicles passing your node
- Auto-creates a **Device Tracker** (GPS position on map) per vehicle
- Auto-creates **Sensors** per vehicle: speed, heading, station type, altitude, yaw rate, drive direction, brake/gas state, vehicle dimensions
- Creates **Node sensors** for your node's telemetry: temperature and uptime
- Stores long-term statistics (min/max/mean) for all numeric sensors via HA Recorder
- Configurable sensor selection per integration via UI

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

### Sensor Selection

After setup, click **Configure** on the integration to choose which CAM fields to expose as sensors:

- Speed, Heading, Station Type *(default)*
- Altitude, Yaw Rate, Drive Direction
- Brake Engaged, Gas Engaged
- Vehicle Length, Vehicle Width

Changes take effect for newly seen vehicles.

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
| `sensor.otm_<stationId>_vehicle_length` | m | Vehicle length |
| `sensor.otm_<stationId>_vehicle_width` | m | Vehicle width |

### Node Device

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.otm_<nodeId>_temp` | °C | Node temperature |
| `sensor.otm_<nodeId>_rbt` | s | Node uptime counter |

---

## Map Card

Add a Map card to your dashboard and select `device_tracker.otm_*` entities to see vehicle positions in real time. Entities only appear after the first vehicle message is received — the map will be empty until a vehicle passes your node.

---

## Statistics

Numeric sensors (speed, heading, altitude, etc.) have `state_class: measurement` set, so Home Assistant automatically records long-term statistics. Access via:

**Developer Tools → Statistics** or add a **Statistics Graph Card** to your dashboard to view min/max/mean over time.

---

## How It Works

Vehicles equipped with V2X hardware (ITS-G5 / IEEE 802.11p) broadcast ETSI ITS CAM (Cooperative Awareness Messages) at up to 10 Hz. The opentrafficmap.org roadside unit at your node receives and decodes these packets, then forwards them as JSON to the MQTT broker. This integration subscribes to your node's topic and parses the decoded data into Home Assistant entities.

---

## License

MIT
