import os
import yaml
import threading
from typing import Any, Dict, Optional


class ConfigManager:
    """
    Singleton ConfigManager for ComfyUI-StalkerVr.
    Loads and merges config.yaml (public) and secrets.yaml (private).
    Thread-safe lazy initialization.
    """
    _instance = None
    _lock = threading.Lock()
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Loads configs from data/ folder."""
        # Path to the root directory (assuming this file is in nodes/)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, "config")
        self._config = {}

        # 1. Load public settings
        self._load_yaml(os.path.join(data_dir, "config.yaml"))

        # 2. Load private secrets (overrides public settings)
        self._load_yaml(os.path.join(data_dir, "secrets.yaml"))

    def _load_yaml(self, path: str):
        """Safely loads YAML and deeply merges with current config."""
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    self._config = self._deep_merge(self._config, data)
        except Exception as e:
            print(f"[ConfigManager] ⚠️ Warning: Failed to load {os.path.basename(path)}: {e}")

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Recursively merges dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets value by dot-path.
        Example: config.get("logging.global_enabled", True)
        """
        keys = key.split('.')
        current = self._config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def reload(self):
        """Force reload configs (useful for development)."""
        with self._lock:
            self._initialize()

    def __repr__(self):
        return f"ConfigManager(sections={list(self._config.keys())})"