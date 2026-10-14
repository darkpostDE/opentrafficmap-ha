DOMAIN = "opentrafficmap"

CONF_VEHICLE_TOPIC = "vehicle_topic"
CONF_STATS_TOPIC = "stats_topic"
CONF_ENABLED_SENSORS = "enabled_sensors"
CONF_VEHICLE_TTL = "vehicle_ttl"

DEFAULT_VEHICLE_TTL = 300  # seconds; 0 = never remove

DATA_MQTT_CLIENT = "mqtt_client"
DATA_ADD_VEHICLE_ENTITIES = "add_vehicle_entities"
DATA_ADD_STATS_ENTITIES = "add_stats_entities"
DATA_KNOWN_STATIONS = "known_stations"

ALL_CAM_SENSORS = [
    "speed",
    "heading",
    "station_type",
    "altitude",
    "yaw_rate",
    "drive_direction",
    "brake_engaged",
    "gas_engaged",
    "emergency_brake_engaged",
    "collision_warning_engaged",
    "acc_engaged",
    "cruise_control_engaged",
    "speed_limiter_engaged",
    "vehicle_length",
    "vehicle_width",
]

DEFAULT_ENABLED_SENSORS = ["speed", "heading", "station_type"]

STATION_TYPE_LABELS = {
    "0": "Unknown",
    "1": "Pedestrian",
    "2": "Cyclist",
    "3": "Moped",
    "4": "Motorcycle",
    "5": "Passenger Car",
    "6": "Bus",
    "7": "Light Truck",
    "8": "Heavy Truck",
    "9": "Trailer",
    "10": "Special Vehicle",
    "11": "Tram",
    "15": "RSU",
}

ALL_AGG_SENSORS = [
    "vehicles_total",
    "speed_avg",
    "speed_max",
    "emergency_brakes",
    "collision_warnings",
    "station_type_counts",
    "debug",
]

