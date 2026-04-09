import logging
from datetime import datetime
from typing import Dict, List, Set

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, create_engine, delete, insert, select, text, update

from config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER


DATABASE_URL = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

processed_agent_data = Table(
    'processed_agent_data',
    metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('road_state', String),
    Column('user_id', Integer),
    Column('x', Float),
    Column('y', Float),
    Column('z', Float),
    Column('latitude', Float),
    Column('longitude', Float),
    Column('timestamp', DateTime),
)


class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    user_id: int = 1
    accelerometer: AccelerometerData
    gps: GpsData
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


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData


class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


app = FastAPI(title='Store Service')
subscriptions: Dict[int, Set[WebSocket]] = {}


@app.on_event('startup')
def ensure_schema():
    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS processed_agent_data ADD COLUMN IF NOT EXISTS user_id INTEGER NOT NULL DEFAULT 1'))
    except Exception:
        logging.exception('Failed to ensure Store schema is up to date')


async def _accept_and_send_history(websocket: WebSocket, user_id: int):
    await websocket.accept()
    subscriptions.setdefault(user_id, set()).add(websocket)

    with engine.connect() as conn:
        query = (
            select(processed_agent_data)
            .where(processed_agent_data.c.user_id == user_id)
            .order_by(processed_agent_data.c.id.desc())
            .limit(200)
        )
        result = conn.execute(query).fetchall()

    payload = [dict(row._mapping) for row in reversed(result)]
    await websocket.send_json(jsonable_encoder(payload))


@app.websocket('/ws/{user_id}')
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await _accept_and_send_history(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.get(user_id, set()).discard(websocket)


@app.websocket('/ws/')
async def websocket_endpoint_default(websocket: WebSocket):
    await websocket_endpoint(websocket, 1)


async def send_data_to_subscribers(user_id: int, data: list[dict]):
    dead_connections: list[WebSocket] = []
    for websocket in subscriptions.get(user_id, set()):
        try:
            await websocket.send_json(jsonable_encoder(data))
        except Exception:
            dead_connections.append(websocket)
    for websocket in dead_connections:
        subscriptions.get(user_id, set()).discard(websocket)


@app.post('/processed_agent_data/')
async def create_processed_agent_data(request: Request):
    payload = await request.json()

    if isinstance(payload, list):
        raw_items = payload
        user_id = 1
    elif isinstance(payload, dict):
        raw_items = payload.get('data', [])
        user_id = int(payload.get('user_id', 1))
    else:
        raise HTTPException(status_code=400, detail='Invalid payload format')

    items = [ProcessedAgentData.model_validate(item) for item in raw_items]
    created_rows: List[dict] = []

    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            for item in items:
                record_user_id = item.agent_data.user_id or user_id
                query = insert(processed_agent_data).values(
                    road_state=item.road_state,
                    user_id=record_user_id,
                    x=item.agent_data.accelerometer.x,
                    y=item.agent_data.accelerometer.y,
                    z=item.agent_data.accelerometer.z,
                    latitude=item.agent_data.gps.latitude,
                    longitude=item.agent_data.gps.longitude,
                    timestamp=item.agent_data.timestamp,
                )
                result = conn.execute(query.returning(processed_agent_data))
                created_rows.append(dict(result.fetchone()._mapping))
            transaction.commit()
        except Exception as exc:
            transaction.rollback()
            logging.exception('Failed to save processed data: %s', exc)
            raise HTTPException(status_code=500, detail='Failed to save processed data') from exc

    if created_rows:
        await send_data_to_subscribers(user_id, created_rows)
    return created_rows


@app.get('/processed_agent_data/{processed_agent_data_id}', response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    with engine.connect() as conn:
        query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = conn.execute(query).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail='Data not found')
        return dict(result._mapping)


@app.get('/processed_agent_data/', response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data():
    with engine.connect() as conn:
        query = select(processed_agent_data).order_by(processed_agent_data.c.id)
        result = conn.execute(query).fetchall()
        return [dict(row._mapping) for row in result]


@app.put('/processed_agent_data/{processed_agent_data_id}', response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            query = update(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id).values(
                road_state=data.road_state,
                user_id=data.agent_data.user_id,
                x=data.agent_data.accelerometer.x,
                y=data.agent_data.accelerometer.y,
                z=data.agent_data.accelerometer.z,
                latitude=data.agent_data.gps.latitude,
                longitude=data.agent_data.gps.longitude,
                timestamp=data.agent_data.timestamp,
            )
            result = conn.execute(query)
            if result.rowcount == 0:
                transaction.rollback()
                raise HTTPException(status_code=404, detail='Data not found')
            transaction.commit()

            fetch_query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
            updated_result = conn.execute(fetch_query).fetchone()
            return dict(updated_result._mapping)
        except HTTPException:
            raise
        except Exception as exc:
            transaction.rollback()
            logging.exception('Failed to update processed data: %s', exc)
            raise HTTPException(status_code=500, detail='Failed to update processed data') from exc


@app.delete('/processed_agent_data/{processed_agent_data_id}', response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            fetch_query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
            to_delete = conn.execute(fetch_query).fetchone()
            if to_delete is None:
                transaction.rollback()
                raise HTTPException(status_code=404, detail='Data not found')

            delete_query = delete(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
            conn.execute(delete_query)
            transaction.commit()
            return dict(to_delete._mapping)
        except HTTPException:
            raise
        except Exception as exc:
            transaction.rollback()
            logging.exception('Failed to delete processed data: %s', exc)
            raise HTTPException(status_code=500, detail='Failed to delete processed data') from exc


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
