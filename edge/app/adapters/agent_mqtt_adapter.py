import logging
from paho.mqtt import client as mqtt_client

from app.entities.agent_data import RawAgentData
from app.interfaces.agent_gateway import AgentGateway
from app.interfaces.hub_gateway import HubGateway
from app.usecases.data_processing import process_agent_data


class AgentMqttAdapter(AgentGateway):
    def __init__(self, broker_host: str, broker_port: int, topic: str, hub_gateway: HubGateway):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.hub_gateway = hub_gateway
        self.client = mqtt_client.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self.on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker (%s:%s)", self.broker_host, self.broker_port)
            client.subscribe(self.topic)
            logging.info("Subscribed to topic `%s`", self.topic)
        else:
            logging.error("Failed to connect, return code %s", rc)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        logging.info("Received raw message from `%s`: %s", self.topic, payload)

        raw_data = RawAgentData.model_validate_json(payload)
        processed_data = process_agent_data(raw_data)
        self.hub_gateway.save_data(processed_data)

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port)

    def start(self):
        self.client.loop_forever()

    def stop(self):
        self.client.disconnect()