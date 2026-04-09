import logging
from typing import List
import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url: str, timeout: int = 10):
        self.api_base_url = api_base_url.rstrip('/')
        self.timeout = timeout

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        if not processed_agent_data_batch:
            return False

        user_id = processed_agent_data_batch[0].agent_data.user_id
        payload = {
            'data': [item.model_dump(mode='json') for item in processed_agent_data_batch],
            'user_id': user_id,
        }

        try:
            response = requests.post(
                f'{self.api_base_url}/processed_agent_data/',
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logging.info('Saved %s records to Store API for user_id=%s', len(processed_agent_data_batch), user_id)
            return True
        except requests.RequestException as exc:
            logging.exception('Failed to save batch to Store API: %s', exc)
            return False
