CREATE TABLE processed_agent_data (
    id SERIAL PRIMARY KEY,
    road_state VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL DEFAULT 1,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    timestamp TIMESTAMP
);
