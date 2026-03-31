from abc import ABC, abstractmethod
from app.entities.agent_data import ProcessedAgentData


class HubGateway(ABC):
    @abstractmethod
    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        pass