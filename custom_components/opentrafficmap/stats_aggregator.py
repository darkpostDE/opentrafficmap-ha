from __future__ import annotations
import json
import logging
import os
import copy
from datetime import datetime, timezone

_LOGGER = logging.getLogger(__name__)

DEFAULT_STATS = {
    "vehicles_total": 0,
    "speed_sum": 0.0,
    "speed_count": 0,
    "speed_max": 0.0,
    "emergency_brakes": 0,
    "collision_warnings": 0,
    "station_type_counts": {},
}


class OtmStatsAggregator:
    def __init__(self, node_id: str, config_dir: str) -> None:
        self._node_id = node_id
        self._path = os.path.join(config_dir, f"stats_{node_id}.json")
        self._data = copy.deepcopy(DEFAULT_STATS)
        self._loaded = False
        self._last_vehicle: dict | None = None
        self._last_seen: str | None = None
        self._known_stations: set[str] = set()

    def _load(self) -> None:
        try:
            with open(self._path) as f:
                saved = json.load(f)
                for k, v in DEFAULT_STATS.items():
                    self._data[k] = saved.get(k, v)
            _LOGGER.debug("Stats loaded from %s: %s", self._path, self._data)
        except FileNotFoundError:
            _LOGGER.debug("No stats file at %s, starting fresh", self._path)
        except Exception as e:
            _LOGGER.warning("Failed to load stats from %s: %s", self._path, e)

    def _save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f)
        except Exception as e:
            _LOGGER.warning("Failed to save stats to %s: %s", self._path, e)

    def update(self, parsed: dict) -> list[tuple[str, dict]]:
        """Update aggregations. Returns list of (event_type, event_data) to fire."""
        if not self._loaded:
            self._load()
            self._loaded = True
        events = []
        sid = parsed["station_id"]
        speed = parsed.get("speed", 0.0)
        prev_max = self._data["speed_max"]

        # new vehicle
        is_new = sid not in self._known_stations
        if is_new:
            self._known_stations.add(sid)
            self._data["vehicles_total"] += 1
            events.append(("otm_new_vehicle", {
                "station_id": sid,
                "speed": round(speed, 1),
                "station_type": parsed.get("station_type"),
                "lat": parsed.get("lat"),
                "lon": parsed.get("lon"),
            }))

        # speed aggregation
        self._data["speed_sum"] += speed
        self._data["speed_count"] += 1
        if speed > self._data["speed_max"]:
            self._data["speed_max"] = round(speed, 1)
            events.append(("otm_speed_record", {
                "station_id": sid,
                "speed": round(speed, 1),
                "previous_max": round(prev_max, 1),
            }))

        # safety events
        if parsed.get("emergency_brake_engaged"):
            self._data["emergency_brakes"] += 1
            events.append(("otm_emergency_brake", {
                "station_id": sid,
                "speed": round(speed, 1),
                "lat": parsed.get("lat"),
                "lon": parsed.get("lon"),
            }))

        if parsed.get("collision_warning_engaged"):
            self._data["collision_warnings"] += 1
            events.append(("otm_collision_warning", {
                "station_id": sid,
                "speed": round(speed, 1),
                "lat": parsed.get("lat"),
                "lon": parsed.get("lon"),
            }))

        # station type counts — only on first sight
        if is_new:
            stype = str(parsed.get("station_type", "unknown"))
            counts = self._data["station_type_counts"]
            counts[stype] = counts.get(stype, 0) + 1

        self._last_vehicle = parsed
        self._last_seen = datetime.now(timezone.utc).isoformat()
        self._save()
        return events

    @property
    def vehicles_total(self) -> int:
        return self._data["vehicles_total"]

    @property
    def speed_avg(self) -> float | None:
        if self._data["speed_count"] == 0:
            return None
        return round(self._data["speed_sum"] / self._data["speed_count"], 1)

    @property
    def speed_max(self) -> float:
        return self._data["speed_max"]

    @property
    def emergency_brakes(self) -> int:
        return self._data["emergency_brakes"]

    @property
    def collision_warnings(self) -> int:
        return self._data["collision_warnings"]

    @property
    def station_type_counts(self) -> str:
        return json.dumps(self._data["station_type_counts"])

    @property
    def debug_attributes(self) -> dict:
        return {
            "last_vehicle": self._last_vehicle,
            "last_seen": self._last_seen,
            "known_stations": len(self._known_stations),
        }
