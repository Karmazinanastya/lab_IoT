import logging
from threading import Lock
from typing import List
from app.entities.agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class BatchProcessor:
    def __init__(self, store_gateway: StoreGateway, batch_size: int = 10):
        self.store_gateway = store_gateway
        self.batch_size = batch_size
        self._buffer: List[ProcessedAgentData] = []
        self._lock = Lock()

    def add(self, item: ProcessedAgentData) -> bool:
        with self._lock:
            self._buffer.append(item)
            current_size = len(self._buffer)
            logging.info("Buffered item. Current batch size: %s/%s", current_size, self.batch_size)
            if current_size < self.batch_size:
                return False

            batch = list(self._buffer)
            if self.store_gateway.save_data(batch):
                self._buffer.clear()
                logging.info("Batch flushed successfully")
                return True

            logging.warning("Batch flush failed. Buffer retained for retry")
            return False

    def flush(self) -> bool:
        with self._lock:
            if not self._buffer:
                return True
            batch = list(self._buffer)
            if self.store_gateway.save_data(batch):
                self._buffer.clear()
                logging.info("Manual flush successful")
                return True
            logging.warning("Manual flush failed")
            return False

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [item.model_dump(mode="json") for item in self._buffer]
