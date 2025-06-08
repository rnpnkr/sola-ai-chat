from typing import Set, Dict
import asyncio
import logging
from backend.subconscious.background_processor import PersistentSubconsciousProcessor

logger = logging.getLogger(__name__)

class UserSessionManager:
    """Manages user sessions and background processing lifecycle"""
    def __init__(self, subconscious_processor: PersistentSubconsciousProcessor):
        self.subconscious_processor = subconscious_processor
        self.active_users: Set[str] = set()
        self.user_sessions: Dict[str, dict] = {}
    async def start_user_session(self, user_id: str):
        """Start background processing for a user"""
        if user_id not in self.active_users:
            self.active_users.add(user_id)
            # Start background subconscious processing
            asyncio.create_task(
                self.subconscious_processor.start_continuous_processing(user_id)
            )
            logger.info(f"Started user session with background processing: {user_id}")
    async def end_user_session(self, user_id: str):
        """End background processing for a user"""
        if user_id in self.active_users:
            self.active_users.remove(user_id)
            self.subconscious_processor.stop_processing(user_id)
            logger.info(f"Ended user session: {user_id}")
    def get_active_users(self) -> Set[str]:
        """Get list of users with active background processing"""
        return self.active_users.copy() 