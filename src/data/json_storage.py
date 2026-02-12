"""JSON file-based storage implementation for player data."""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.data.storage_interface import PlayerStorage


class JSONStorage(PlayerStorage):
    """JSON file-based player storage implementation."""

    def __init__(self, data_dir: str = "data/players"):
        """Initialize JSON storage.

        Args:
            data_dir: Directory to store player JSON files
        """
        self.data_dir = data_dir
        self.combat_dir = os.path.join(os.path.dirname(data_dir), 'combat_sessions')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.combat_dir, exist_ok=True)

    def _get_player_file(self, player_id: str) -> str:
        """Get file path for player data."""
        return os.path.join(self.data_dir, f'{player_id}.json')

    def _serialize_player(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize player data for JSON storage."""
        data = player_data.copy()

        # Handle enum types
        if 'stage' in data and hasattr(data['stage'], 'value'):
            data['stage'] = data['stage'].value
        elif 'stage' in data and isinstance(data['stage'], str):
            pass  # Already string

        if 'sect' in data and hasattr(data['sect'], 'value'):
            data['sect'] = data['sect'].value
        elif 'sect' in data and isinstance(data['sect'], str):
            pass  # Already string

        # Handle datetime
        for key in ['created_at', 'last_active']:
            if key in data and hasattr(data[key], 'isoformat'):
                data[key] = data[key].isoformat()

        return data

    def save(self, player_id: str, data: Dict[str, Any]) -> bool:
        """Save player data to JSON file."""
        try:
            # Ensure player_id is in data
            data['player_id'] = player_id

            # Serialize data
            serializable_data = self._serialize_player(data)

            file_path = self._get_player_file(player_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"JSON save failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Load player data by ID from JSON file."""
        try:
            file_path = self._get_player_file(player_id)
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON load failed: {e}")
            return None

    def load_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Load player data by name from JSON files."""
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.data_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('name') == name:
                            return data
            return None
        except Exception as e:
            print(f"JSON load_by_name failed: {e}")
            return None

    def list_all(self) -> List[str]:
        """List all player IDs from JSON files."""
        player_ids = []
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.data_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'player_id' in data:
                            player_ids.append(data['player_id'])
        except Exception as e:
            print(f"JSON list_all failed: {e}")
        return player_ids

    def delete(self, player_id: str) -> bool:
        """Delete player JSON file."""
        try:
            file_path = self._get_player_file(player_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"JSON delete failed: {e}")
            return False

    # Combat session methods
    def _get_combat_session_file(self, session_id: str) -> str:
        """Get file path for combat session data."""
        return os.path.join(self.combat_dir, f'{session_id}.json')

    def save_combat_session(self, session_id: str, player_name: str, state: Dict[str, Any]) -> bool:
        """Save combat session state to JSON file."""
        try:
            session_data = {
                'session_id': session_id,
                'player_name': player_name,
                'state': state,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            file_path = self._get_combat_session_file(session_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"JSON save_combat_session failed: {e}")
            return False

    def load_combat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load combat session by ID from JSON file."""
        try:
            file_path = self._get_combat_session_file(session_id)
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON load_combat_session failed: {e}")
            return None

    def load_combat_session_by_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Load active combat session for a player from JSON files."""
        try:
            for filename in os.listdir(self.combat_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.combat_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('player_name') == player_name:
                            return data
            return None
        except Exception as e:
            print(f"JSON load_combat_session_by_player failed: {e}")
            return None

    def delete_combat_session(self, session_id: str) -> bool:
        """Delete combat session JSON file."""
        try:
            file_path = self._get_combat_session_file(session_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"JSON delete_combat_session failed: {e}")
            return False

    def cleanup_old_combat_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old combat sessions."""
        cleaned = 0
        try:
            now = datetime.now()
            for filename in os.listdir(self.combat_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.combat_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        created_at_str = data.get('created_at')
                        if created_at_str:
                            created_at = datetime.fromisoformat(created_at_str)
                            age_hours = (now - created_at).total_seconds() / 3600
                            if age_hours > max_age_hours:
                                os.remove(file_path)
                                cleaned += 1
                    except Exception:
                        # If we can't parse the file, remove it
                        os.remove(file_path)
                        cleaned += 1
        except Exception as e:
            print(f"JSON cleanup_old_combat_sessions failed: {e}")
        return cleaned


# Backward compatibility - module-level functions using default storage
_default_storage = None


def _get_default_storage() -> JSONStorage:
    """Get or create default storage instance."""
    global _default_storage
    if _default_storage is None:
        data_dir = os.path.join(os.path.dirname(__file__), '../../data/players')
        _default_storage = JSONStorage(data_dir)
    return _default_storage


def save_player(player_data: Dict[str, Any]) -> bool:
    """Save player data (backward compatibility)."""
    player_id = player_data.get('player_id')
    if not player_id:
        return False
    return _get_default_storage().save(player_id, player_data)


def load_player(player_id: str) -> Optional[Dict[str, Any]]:
    """Load player data by ID (backward compatibility)."""
    return _get_default_storage().load(player_id)


def load_player_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Load player data by name (backward compatibility)."""
    return _get_default_storage().load_by_name(name)


def list_all_players() -> List[Dict[str, Any]]:
    """List all player data (backward compatibility)."""
    players = []
    storage = _get_default_storage()
    for player_id in storage.list_all():
        data = storage.load(player_id)
        if data:
            players.append(data)
    return players
