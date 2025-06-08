from typing import Dict, Optional
from .mem0_async_service import IntimateMemoryService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationMemoryManager:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    async def store_intimate_conversation(
        self,
        user_message: str,
        ai_response: str,
        user_id: str,
        emotional_context: Dict = None
    ) -> Optional[str]:
        """Store conversation using coordinated memory operations"""
        conversation_messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ]
        # Add emotional and contextual metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "conversation_type": "intimate_companion",
            "emotional_context": emotional_context or {},
            "intimacy_level": self._assess_intimacy_level(user_message, ai_response)
        }
        try:
            # Use memory coordinator instead of direct storage
            from services.memory_coordinator import get_memory_coordinator
            coordinator = get_memory_coordinator()
            operation_id = await coordinator.schedule_memory_operation(
                user_id=user_id,
                operation_type="conversation_memory",
                content={
                    "messages": conversation_messages,
                    "metadata": metadata
                },
                priority=1  # High priority for conversation memory
            )
            logger.info(f"Scheduled intimate memory storage for user {user_id}: {operation_id}")
            return operation_id
        except Exception as e:
            logger.error(f"Failed to schedule memory storage: {e}")
            return None

    def _assess_intimacy_level(self, user_message: str, ai_response: str) -> str:
        """Assess the intimacy level of the conversation"""
        intimate_indicators = [
            "feel", "lonely", "scared", "worried", "excited", "grateful",
            "love", "miss", "remember", "share", "personal", "private"
        ]

        combined_text = f"{user_message} {ai_response}".lower()
        intimate_count = sum(1 for indicator in intimate_indicators if indicator in combined_text)

        if intimate_count >= 3:
            return "high"
        elif intimate_count >= 1:
            return "medium"
        else:
            return "low" 