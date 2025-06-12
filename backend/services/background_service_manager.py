import asyncio
import logging
from typing import Set
from subconscious.background_processor import PersistentSubconsciousProcessor
from services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class BackgroundServiceManager:
    """Global manager for background services that should persist across conversations"""
    def __init__(self):
        self.mem0_service = ServiceRegistry.get_memory_service()
        self.subconscious_processor = PersistentSubconsciousProcessor(self.mem0_service)
        self.active_users: Set[str] = set()
        self._shutdown_event = asyncio.Event()
    async def ensure_user_background_processing(self, user_id: str) -> bool:
        """Ensure background processing is running for user (idempotent)"""
        try:
            if user_id not in self.active_users:
                self.active_users.add(user_id)
                # Start background processing
                asyncio.create_task(
                    self._managed_background_processing(user_id)
                )
                logger.info(f"Started managed background processing for {user_id}")
                return True
            else:
                logger.debug(f"Background processing already managed for {user_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to ensure background processing for {user_id}: {e}")
            return False
    async def _managed_background_processing(self, user_id: str):
        """Managed wrapper for background processing with cleanup"""
        try:
            await self.subconscious_processor.start_continuous_processing(user_id)
        except Exception as e:
            logger.error(f"Background processing failed for {user_id}: {e}")
        finally:
            # Cleanup when processing ends
            self.active_users.discard(user_id)
            logger.info(f"Cleaned up background processing for {user_id}")
    def stop_user_processing(self, user_id: str):
        """Stop background processing for a specific user"""
        if user_id in self.active_users:
            self.subconscious_processor.stop_processing(user_id)
            self.active_users.discard(user_id)
            logger.info(f"Stopped background processing for {user_id}")
    async def shutdown_all(self):
        """Gracefully shutdown all background processing"""
        logger.info("Shutting down all background processing...")
        for user_id in self.active_users.copy():
            self.stop_user_processing(user_id)
        self._shutdown_event.set()
    def get_active_users(self) -> Set[str]:
        """Get set of users with active background processing"""
        return self.active_users.copy()
    async def coordinate_with_realtime_analysis(self, user_id: str):
        """Coordinate background processing with real-time analysis"""
        try:
            # If real-time analysis is happening, delay background processing slightly
            # to avoid conflicts with scaffold updates
            if user_id in self.active_users:
                logger.debug(f"Coordinating background processing with real-time analysis for {user_id}")
                await asyncio.sleep(0.5)  # Small delay for coordination
        except Exception as e:
            logger.error(f"Error coordinating processing for {user_id}: {e}")

    # ---------------------- Health reporting --------------------------
    def get_stats(self) -> dict:
        """Return simple stats for health endpoint."""
        return {
            "active_users": len(self.active_users),
        }

# Global instance
background_service_manager = BackgroundServiceManager() 