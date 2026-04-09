from app.entities.agent_data import AgentData, ProcessedAgentData, RawAgentData


_last_detection_state: dict[int, bool] = {}


def detect_road_state(raw_data: RawAgentData) -> str:
    user_id = raw_data.user_id
    road_state = 'normal'
    last_detection_state = _last_detection_state.get(user_id, False)

    if raw_data.accelerometer.z < 0.6:
        road_state = 'pothole'
    elif raw_data.accelerometer.z > 1.2:
        road_state = 'bump'

    detection_happened = road_state != 'normal'
    if not (not last_detection_state and detection_happened):
        road_state = 'normal'

    _last_detection_state[user_id] = detection_happened
    return road_state


def process_agent_data(raw_data: RawAgentData) -> ProcessedAgentData:
    return ProcessedAgentData(
        road_state=detect_road_state(raw_data),
        agent_data=AgentData(
            user_id=raw_data.user_id,
            accelerometer=raw_data.accelerometer,
            gps=raw_data.gps,
            timestamp=raw_data.time,
        ),
    )
