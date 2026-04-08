import asyncio
import json
from datetime import datetime

import websockets
from kivy import Logger
from pydantic import BaseModel, field_validator

from config import STORE_HOST, STORE_PORT


class ProcessedAgentData(BaseModel):
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

    @classmethod
    @field_validator('timestamp', mode='before')
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError('Invalid timestamp format. Expected ISO 8601 format.') from exc


class Datasource:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.connection_status = 'Disconnected'
        self._new_points = []
        asyncio.ensure_future(self.connect_to_server())

    def get_new_points(self):
        points = self._new_points
        self._new_points = []
        return points

    async def connect_to_server(self):
        uri = f'ws://{STORE_HOST}:{STORE_PORT}/ws/{self.user_id}'
        while True:
            try:
                Logger.info(f'MapView: connecting to {uri}')
                async with websockets.connect(uri) as websocket:
                    self.connection_status = 'Connected'
                    while True:
                        message = await websocket.recv()
                        self.handle_received_data(message)
            except Exception as exc:
                self.connection_status = 'Disconnected'
                Logger.warning(f'MapView: websocket reconnect after error: {exc}')
                await asyncio.sleep(2)

    def handle_received_data(self, message):
        Logger.debug(f'Received data: {message}')
        parsed = message
        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        if isinstance(parsed, dict):
            parsed = [parsed]
        elif isinstance(parsed, str):
            parsed = json.loads(parsed)
            if isinstance(parsed, dict):
                parsed = [parsed]

        processed_agent_data_list = sorted(
            [ProcessedAgentData(**item) for item in parsed],
            key=lambda value: value.timestamp,
        )
        new_points = [
            (
                item.latitude,
                item.longitude,
                item.road_state,
                item.user_id,
            )
            for item in processed_agent_data_list
        ]
        self._new_points.extend(new_points)
