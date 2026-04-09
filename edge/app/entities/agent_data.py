from datetime import datetime
from pydantic import BaseModel, field_validator


class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    longitude: float
    latitude: float


class ParkingData(BaseModel):
    empty_count: int
    gps: GpsData


class RawAgentData(BaseModel):
    user_id: int = 1
    accelerometer: AccelerometerData
    gps: GpsData
    parking: ParkingData
    time: datetime

    @classmethod
    @field_validator('time', mode='before')
    def parse_time(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError('Invalid time format. Expected ISO 8601 datetime.') from exc


class AgentData(BaseModel):
    user_id: int = 1
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator('timestamp', mode='before')
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError('Invalid timestamp format. Expected ISO 8601 datetime.') from exc


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData
