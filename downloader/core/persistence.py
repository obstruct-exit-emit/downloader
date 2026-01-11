# Persistence for download queue and history
import os
import json
import uuid
from .utils import STATE_PATH


class Persistence:
    def __init__(self, path=None):
        self.path = os.fspath(path or STATE_PATH)
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({'queue': [], 'history': []}, f)

    def load(self):
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ensure_file()
            return {'queue': [], 'history': []}

    def save(self, queue, history):
        with open(self.path, 'w') as f:
            json.dump({'queue': queue, 'history': history}, f)

    def generate_id(self):
        return str(uuid.uuid4())
