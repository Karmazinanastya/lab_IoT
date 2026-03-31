from abc import ABC, abstractmethod
from typing import List
from app.entities.processed_agent_data import ProcessedAgentData


class StoreGateway(ABC):
    @abstractmethod
    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        pass