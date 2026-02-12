"""Storage factory for creating storage backend instances."""

import os
import yaml
from typing import Optional

from src.data.storage_interface import PlayerStorage
from src.data.json_storage import JSONStorage
from src.data.sqlite_storage import SQLiteStorage


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        '../../config/settings.yaml'
    )

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            # File might be in Python-style format, return defaults
            return {}
    return {}


# Singleton storage instance
_storage_instance: Optional[PlayerStorage] = None


def get_storage() -> PlayerStorage:
    """Get storage instance based on configuration.

    Returns:
        PlayerStorage instance (JSON or SQLite based on config)
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    config = load_config()
    storage_config = config.get('storage', {})
    storage_type = storage_config.get('type', 'json')

    if storage_type == 'sqlite':
        db_path = storage_config.get('path', 'data/game.db')
        _storage_instance = SQLiteStorage(db_path)
    else:
        data_dir = storage_config.get('path', 'data/players')
        _storage_instance = JSONStorage(data_dir)

    return _storage_instance


def reset_storage():
    """Reset storage instance (useful for testing)."""
    global _storage_instance
    _storage_instance = None
