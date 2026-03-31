import os


def try_parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST") or "mqtt"
MQTT_BROKER_PORT = try_parse_int(os.environ.get("MQTT_BROKER_PORT"), 1883)
MQTT_TOPIC = os.environ.get("MQTT_TOPIC") or "processed_data_topic"

STORE_API_HOST = os.environ.get("STORE_API_HOST") or "store"
STORE_API_PORT = try_parse_int(os.environ.get("STORE_API_PORT"), 8000)
STORE_API_BASE_URL = f"http://{STORE_API_HOST}:{STORE_API_PORT}"

BATCH_SIZE = try_parse_int(os.environ.get("BATCH_SIZE"), 10)
HTTP_PORT = try_parse_int(os.environ.get("HTTP_PORT"), 8001)
LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"