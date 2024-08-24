import json
import os
import logging
from typing import Dict, Any

class LocalStorageManager:
    def __init__(self, storage_file: str = 'local_data.json'):
        self.storage_file = storage_file
        self.data: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_data()

    def _load_data(self):
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
            self.logger.info(f"Loaded local data with {len(self.data)} entries")
        except Exception as e:
            self.logger.error(f"Error loading local data: {str(e)}")
            self.data = {}

    def _save_data(self):
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.data, f)
            self.logger.info(f"Saved local data with {len(self.data)} entries")
        except Exception as e:
            self.logger.error(f"Error saving local data: {str(e)}")

    def get_company_data(self, company_id: str) -> Dict[str, Any]:
        return self.data.get(company_id, {})

    def update_company_data(self, company_id: str, new_data: Dict[str, Any]):
        if company_id not in self.data:
            self.data[company_id] = {}
        self.data[company_id].update(new_data)
        self._save_data()
        self.logger.info(f"Updated local data for company {company_id}")

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        return self.data