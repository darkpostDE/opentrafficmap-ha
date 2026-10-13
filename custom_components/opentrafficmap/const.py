DOMAIN = "opentrafficmap"

CONF_VEHICLE_TOPIC = "vehicle_topic"
CONF_STATS_TOPIC = "stats_topic"
CONF_ENABLED_SENSORS = "enabled_sensors"

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
    "vehicle_length",
    "vehicle_width",
]

DEFAULT_ENABLED_SENSORS = ["speed", "heading", "station_type"]
