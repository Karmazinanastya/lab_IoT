import json
import logging
from paho.mqtt import client as mqtt_client

from app.entities.agent_data import ProcessedAgentData
from app.interfaces.hub_gateway import HubGateway


class HubMqttAdapter(HubGateway):
    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt_client.Client()
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        payload = processed_data.model_dump(mode="json")
        result = self.client.publish(self.topic, json.dumps(payload))
        status = result[0]

        if status == 0:
            logging.info("Processed data sent to topic `%s`", self.topic)
            return True

        logging.error("Failed to send processed data to topic `%s`", self.topic)
        return False

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()