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
    ) -> Optional[Dict]:
        """Store conversation with intimate context and emotional metadata"""
        
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
            result = await self.mem0_service.store_conversation_memory(
                messages=conversation_messages,
                user_id=user_id,
                metadata=metadata
            )
            logger.info(f"Stored intimate memory for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
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