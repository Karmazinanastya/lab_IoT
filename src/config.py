import os


def try_parse(type_, value: str | None):
    try:
        return type_(value) if value is not None else None
    except Exception:
        return None


MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST') or 'mqtt'
MQTT_BROKER_PORT = try_parse(int, os.environ.get('MQTT_BROKER_PORT')) or 1883
MQTT_TOPIC = os.environ.get('MQTT_TOPIC') or 'agent_data_topic'

DELAY = try_parse(float, os.environ.get('DELAY')) or 1
USER_ID = try_parse(int, os.environ.get('USER_ID')) or 1
ACCELEROMETER_DIVISOR = try_parse(float, os.environ.get('ACCELEROMETER_DIVISOR')) or 16384.0
