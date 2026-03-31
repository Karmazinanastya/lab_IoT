import json
import logging
from contextlib import asynccontextmanager

import paho.mqtt.client as mqtt
from fastapi import FastAPI

from app.adapters.store_api_adapter import StoreApiAdapter
from app.entities.processed_agent_data import ProcessedAgentData
from app.services.batch_processor import BatchProcessor
from config import (
    BATCH_SIZE,
    HTTP_PORT,
    LOG_LEVEL,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_TOPIC,
    STORE_API_BASE_URL,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
)

store_adapter = StoreApiAdapter(api_base_url=STORE_API_BASE_URL)
batch_processor = BatchProcessor(store_gateway=store_adapter, batch_size=BATCH_SIZE)
mqtt_client: mqtt.Client | None = None


def handle_payload(payload: str) -> None:
    processed_data = ProcessedAgentData.model_validate_json(payload)
    batch_processor.add(processed_data)
    logging.info("Accepted processed message with road_state=%s", processed_data.road_state)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker %s:%s", MQTT_BROKER_HOST, MQTT_BROKER_PORT)
        client.subscribe(MQTT_TOPIC)
        logging.info("Subscribed to topic %s", MQTT_TOPIC)
    else:
        logging.error("Failed to connect to MQTT broker, rc=%s", rc)


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    try:
        handle_payload(payload)
    except Exception:
        logging.exception("Failed to process MQTT message: %s", payload)


def start_mqtt_listener() -> mqtt.Client:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.loop_start()
    return client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client
    mqtt_client = start_mqtt_listener()
    yield
    batch_processor.flush()
    if mqtt_client is not None:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


app = FastAPI(title="Hub Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mqtt_topic": MQTT_TOPIC,
        "batch_size": BATCH_SIZE,
        "store_api": STORE_API_BASE_URL,
    }


@app.get("/buffer")
def buffer_state():
    data = batch_processor.snapshot()
    return {"items": data, "count": len(data)}


@app.post("/ingest")
def ingest(payload: dict):
    handle_payload(json.dumps(payload))
    return {"status": "accepted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)