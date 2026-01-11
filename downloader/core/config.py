# Configuration and persistence for settings (rpc secrets/ports, mega creds)
import json
import os
from pathlib import Path
from .utils import PROJECT_ROOT


def _default_config_path():
    """Return default config path, preferring user config dir if platformdirs is available."""
    try:
        from platformdirs import user_config_dir
        base = Path(user_config_dir("downloader", "downloader"))
    except Exception:
        base = PROJECT_ROOT
    base.mkdir(parents=True, exist_ok=True)
    return base / ".downloader_config.json"


class Config:
    def __init__(self, path=None):
        self.path = Path(path or _default_config_path())
        self.data = {}
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}
        return self.data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def set_aria2(self, *, rpc_secret=None, rpc_port=None):
        section = self.data.setdefault("aria2", {})
        if rpc_secret is not None:
            section["rpc_secret"] = rpc_secret
        if rpc_port is not None:
            if not isinstance(rpc_port, int) or rpc_port < 1 or rpc_port > 65535:
                raise ValueError("rpc_port must be an integer between 1 and 65535")
            section["rpc_port"] = rpc_port
        self.save()

    def get_aria2(self):
        return self.data.get("aria2", {})

    def set_mega(self, *, email=None, password=None):
        section = self.data.setdefault("mega", {})
        if email is not None:
            section["email"] = email
        if password is not None:
            section["password"] = password
        self.save()

    def get_mega(self):
        return self.data.get("mega", {})

