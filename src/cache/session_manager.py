import secrets
from datetime import datetime
from src.cache.redis_client import redis_client
from src.loggers import Logger

logger = Logger(__name__).get_logger()


class SessionManager:
    def __init__(self):
        self.session_prefix = "session:"
        self.session_expiry = 1 * 60  # 1 min for 1 hr -->> 1 * 60 * 60

    def create_session(self, user_id: int, user_data: dict = None) -> str:
        """Create new session and return session token"""
        session_token = secrets.token_urlsafe(32)
        session_key = f"{self.session_prefix}{session_token}"

        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "user_data": user_data or {}
        }

        if redis_client.set_json(session_key, session_data, self.session_expiry):
            logger.info(f"Session created for user {user_id}")
            return session_token
        else:
            logger.error("Failed to create session")
            return None

    def get_session(self, session_token: str) -> dict:
        """Get session data by token"""
        if not session_token:
            return None

        session_key = f"{self.session_prefix}{session_token}"
        session_data = redis_client.get_json(session_key)

        if session_data:
            # Refresh session expiry on access
            redis_client.set_json(session_key, session_data, self.session_expiry)
            return session_data
        return None

    def delete_session(self, session_token: str) -> bool:
        """Delete session by token"""
        session_key = f"{self.session_prefix}{session_token}"
        return redis_client.delete(session_key)

    def get_user_id(self, session_token: str) -> int:
        """Get user ID from session token"""
        session = self.get_session(session_token)
        return session.get("user_id") if session else None

    def is_valid_session(self, session_token: str) -> bool:
        """Check if session is valid"""
        return self.get_session(session_token) is not None


# Global session manager instance
session_manager = SessionManager()
