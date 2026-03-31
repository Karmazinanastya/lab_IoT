import logging

from app.adapters.agent_mqtt_adapter import AgentMqttAdapter
from app.adapters.hub_mqtt_adapter import HubMqttAdapter
from config import (
    LOG_LEVEL,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_TOPIC,
    HUB_MQTT_BROKER_HOST,
    HUB_MQTT_BROKER_PORT,
    HUB_MQTT_TOPIC,
)

if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )

    hub_adapter = HubMqttAdapter(
        broker=HUB_MQTT_BROKER_HOST,
        port=HUB_MQTT_BROKER_PORT,
        topic=HUB_MQTT_TOPIC,
    )

    agent_adapter = AgentMqttAdapter(
        broker_host=MQTT_BROKER_HOST,
        broker_port=MQTT_BROKER_PORT,
        topic=MQTT_TOPIC,
        hub_gateway=hub_adapter,
    )

    try:
        agent_adapter.connect()
        agent_adapter.start()
    except KeyboardInterrupt:
        logging.info("Edge service stopped by user.")
    finally:
        agent_adapter.stop()
        hub_adapter.close()