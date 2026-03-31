import os


def try_parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST") or "mqtt"
MQTT_BROKER_PORT = try_parse_int(os.environ.get("MQTT_BROKER_PORT"), 1883)
MQTT_TOPIC = os.environ.get("MQTT_TOPIC") or "agent_data_topic"

HUB_MQTT_BROKER_HOST = os.environ.get("HUB_MQTT_BROKER_HOST") or "mqtt"
HUB_MQTT_BROKER_PORT = try_parse_int(os.environ.get("HUB_MQTT_BROKER_PORT"), 1883)
HUB_MQTT_TOPIC = os.environ.get("HUB_MQTT_TOPIC") or "processed_data_topic"

LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"