"""SQLite storage implementation for player data."""

import json
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from src.data.storage_interface import PlayerStorage


class SQLiteStorage(PlayerStorage):
    """SQLite-based player storage implementation."""

    def __init__(self, db_path: str = "data/game.db"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_schema()

    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _init_schema(self):
        """Initialize database schema."""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '../../migrations/schema.sql'
        )

        with self._get_connection() as conn:
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
            else:
                # Inline schema if file not found
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS players (
                        player_id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        level INTEGER DEFAULT 1,
                        xp INTEGER DEFAULT 0,
                        stage TEXT DEFAULT '炼气期',
                        sect TEXT,
                        cultivation INTEGER DEFAULT 0,
                        spirit_stones INTEGER DEFAULT 1000,
                        current_map TEXT DEFAULT '宗门',
                        base_stats TEXT,
                        sect_stats TEXT,
                        school_progress TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);

                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    );

                    CREATE TABLE IF NOT EXISTS combat_sessions (
                        session_id TEXT PRIMARY KEY,
                        player_name TEXT NOT NULL,
                        state TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_combat_sessions_player ON combat_sessions(player_name);
                    CREATE INDEX IF NOT EXISTS idx_combat_sessions_status ON combat_sessions(status);
                    CREATE INDEX IF NOT EXISTS idx_combat_sessions_updated ON combat_sessions(updated_at);
                ''')

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _serialize_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare player data for database storage."""
        result = {}

        # Direct columns
        direct_fields = [
            'player_id', 'name', 'level', 'xp', 'stage', 'sect',
            'cultivation', 'spirit_stones', 'current_map'
        ]

        for field in direct_fields:
            value = data.get(field)
            if value is not None:
                # Handle enums
                if hasattr(value, 'value'):
                    result[field] = value.value
                else:
                    result[field] = value

        # JSON columns
        json_fields = ['base_stats', 'sect_stats', 'school_progress']
        for field in json_fields:
            value = data.get(field)
            if value is not None:
                if isinstance(value, str):
                    result[field] = value
                else:
                    result[field] = json.dumps(value, ensure_ascii=False)
            else:
                result[field] = None

        # Timestamps
        if 'created_at' in data:
            result['created_at'] = data['created_at']
        if 'last_active' in data:
            result['last_active'] = data['last_active']

        return result

    def _deserialize_from_db(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to player data dictionary."""
        result = dict(row)

        # Parse JSON columns
        json_fields = ['base_stats', 'sect_stats', 'school_progress']
        for field in json_fields:
            value = result.get(field)
            if value and isinstance(value, str):
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    pass

        return result

    def save(self, player_id: str, data: Dict[str, Any]) -> bool:
        """Save player data to SQLite."""
        try:
            serialized = self._serialize_for_db(data)
            serialized['player_id'] = player_id
            serialized['last_active'] = datetime.now().isoformat()

            if 'created_at' not in serialized or not serialized['created_at']:
                serialized['created_at'] = datetime.now().isoformat()

            columns = list(serialized.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            update_clause = ', '.join([f"{col} = excluded.{col}" for col in columns if col != 'player_id'])

            sql = f'''
                INSERT INTO players ({column_names})
                VALUES ({placeholders})
                ON CONFLICT(player_id) DO UPDATE SET {update_clause}
            '''

            with self._get_connection() as conn:
                conn.execute(sql, [serialized[col] for col in columns])

            return True
        except Exception as e:
            print(f"SQLite save failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Load player data by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM players WHERE player_id = ?',
                    (player_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._deserialize_from_db(row)
            return None
        except Exception as e:
            print(f"SQLite load failed: {e}")
            return None

    def load_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Load player data by name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM players WHERE name = ?',
                    (name,)
                )
                row = cursor.fetchone()
                if row:
                    return self._deserialize_from_db(row)
            return None
        except Exception as e:
            print(f"SQLite load_by_name failed: {e}")
            return None

    def list_all(self) -> List[str]:
        """List all player IDs."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('SELECT player_id FROM players')
                return [row['player_id'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"SQLite list_all failed: {e}")
            return []

    def delete(self, player_id: str) -> bool:
        """Delete player data."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'DELETE FROM players WHERE player_id = ?',
                    (player_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"SQLite delete failed: {e}")
            return False

    # Combat session methods
    def save_combat_session(self, session_id: str, player_name: str, state: dict) -> bool:
        """Save combat session state to SQLite."""
        try:
            import json
            state_json = json.dumps(state, ensure_ascii=False)
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO combat_sessions (session_id, player_name, state, status, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        player_name = excluded.player_name,
                        state = excluded.state,
                        status = excluded.status,
                        updated_at = excluded.updated_at
                ''', (session_id, player_name, state_json, state.get('status', 'active'), now))

            return True
        except Exception as e:
            print(f"SQLite save_combat_session failed: {e}")
            return False

    def load_combat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load combat session by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM combat_sessions WHERE session_id = ?',
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._deserialize_combat_session(row)
            return None
        except Exception as e:
            print(f"SQLite load_combat_session failed: {e}")
            return None

    def load_combat_session_by_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Load active combat session for a player."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM combat_sessions WHERE player_name = ? AND status = 'active' ORDER BY updated_at DESC LIMIT 1",
                    (player_name,)
                )
                row = cursor.fetchone()
                if row:
                    return self._deserialize_combat_session(row)
            return None
        except Exception as e:
            print(f"SQLite load_combat_session_by_player failed: {e}")
            return None

    def delete_combat_session(self, session_id: str) -> bool:
        """Delete combat session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'DELETE FROM combat_sessions WHERE session_id = ?',
                    (session_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"SQLite delete_combat_session failed: {e}")
            return False

    def cleanup_old_combat_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old combat sessions."""
        try:
            cutoff = datetime.now().isoformat()
            # SQLite datetime comparison
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    DELETE FROM combat_sessions
                    WHERE datetime(updated_at) < datetime('now', ? || ' hours')
                ''', (f'-{max_age_hours}',))
                return cursor.rowcount
        except Exception as e:
            print(f"SQLite cleanup_old_combat_sessions failed: {e}")
            return 0

    def _deserialize_combat_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to combat session data."""
        result = dict(row)
        state = result.get('state')
        if state and isinstance(state, str):
            try:
                result['state'] = json.loads(state)
            except json.JSONDecodeError:
                pass
        return result
