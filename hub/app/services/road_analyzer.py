from app.entities.agent_data import AgentData, ProcessedAgentData, RawAgentData


class RoadAnalyzer:
    @staticmethod
    def detect_road_state(raw_data: RawAgentData) -> str:
        ax = abs(raw_data.accelerometer.x)
        ay = abs(raw_data.accelerometer.y)
        az = abs(raw_data.accelerometer.z)
        vibration_score = max(ax, ay, az)

        if vibration_score >= 35:
            return "critical"
        if vibration_score >= 20:
            return "damaged"
        if vibration_score >= 10:
            return "uneven"
        return "good"

    @classmethod
    def process(cls, raw_data: RawAgentData) -> ProcessedAgentData:
        return ProcessedAgentData(
            road_state=cls.detect_road_state(raw_data),
            agent_data=AgentData(
                accelerometer=raw_data.accelerometer,
                gps=raw_data.gps,
                timestamp=raw_data.time,
            ),
        )
