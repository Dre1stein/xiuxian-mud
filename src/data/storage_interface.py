"""Storage interface for player data persistence."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class PlayerStorage(ABC):
    """Abstract base class for player storage implementations."""

    @abstractmethod
    def save(self, player_id: str, data: Dict[str, Any]) -> bool:
        """Save player data.

        Args:
            player_id: Unique player identifier
            data: Player data dictionary

        Returns:
            True if save successful, False otherwise
        """
        pass

    @abstractmethod
    def load(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Load player data by ID.

        Args:
            player_id: Unique player identifier

        Returns:
            Player data dictionary or None if not found
        """
        pass

    @abstractmethod
    def load_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Load player data by name.

        Args:
            name: Player name

        Returns:
            Player data dictionary or None if not found
        """
        pass

    @abstractmethod
    def list_all(self) -> List[str]:
        """List all player IDs.

        Returns:
            List of player IDs
        """
        pass

    @abstractmethod
    def delete(self, player_id: str) -> bool:
        """Delete player data.

        Args:
            player_id: Unique player identifier

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    # Combat session methods
    @abstractmethod
    def save_combat_session(self, session_id: str, player_name: str, state: dict) -> bool:
        """Save combat session state.

        Args:
            session_id: Unique combat session identifier
            player_name: Player name associated with session
            state: Serialized combat session state

        Returns:
            True if save successful, False otherwise
        """
        pass

    @abstractmethod
    def load_combat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load combat session by ID.

        Args:
            session_id: Unique combat session identifier

        Returns:
            Combat session data or None if not found
        """
        pass

    @abstractmethod
    def load_combat_session_by_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Load active combat session for a player.

        Args:
            player_name: Player name

        Returns:
            Combat session data or None if not found
        """
        pass

    @abstractmethod
    def delete_combat_session(self, session_id: str) -> bool:
        """Delete combat session.

        Args:
            session_id: Unique combat session identifier

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def cleanup_old_combat_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old combat sessions.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of sessions cleaned up
        """
        pass
