# Persistence for download queue and history
import os
import json
import uuid

class Persistence:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.path.expanduser('~'), '.downloader_queue.json')
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({'queue': [], 'history': []}, f)

    def load(self):
        with open(self.path, 'r') as f:
            return json.load(f)

    def save(self, queue, history):
        with open(self.path, 'w') as f:
            json.dump({'queue': queue, 'history': history}, f)

    def generate_id(self):
        return str(uuid.uuid4())
