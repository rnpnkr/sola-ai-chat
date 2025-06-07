from typing import Dict, List
from .mem0_async_service import IntimateMemoryService
import logging

logger = logging.getLogger(__name__)

class MemoryContextBuilder:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    async def build_intimate_context(self, current_message: str, user_id: str) -> str:
        """Build memory-informed context for intimate responses"""
        try:
            # Search for relevant emotional memories
            memories = await self.mem0_service.search_intimate_memories(
                query=current_message,
                user_id=user_id,
                limit=3
            )
            
            # Format memories for LLM context
            context = self._format_intimate_memories(memories)
            return context
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return "This is the beginning of your relationship with this person."

    def _format_intimate_memories(self, memories: Dict) -> str:
        """Format memories for intimate conversation context"""
        results = memories.get("results", [])
        
        if not results:
            return "This is the beginning of your relationship with this person."

        formatted_memories = []
        for memory in results:
            memory_text = memory.get("memory", "")
            # Add emotional context from metadata if available
            metadata = memory.get("metadata", {})
            emotional_context = metadata.get("emotional_context", {})
            
            # Enhance memory with emotional context
            if emotional_context:
                context_notes = ", ".join([f"{k}: {v}" for k, v in emotional_context.items()])
                formatted_memories.append(f"• {memory_text} ({context_notes})")
            else:
                formatted_memories.append(f"• {memory_text}")

        return f"""What you remember about this person:
{chr(10).join(formatted_memories)}

Use this context to respond with deep understanding and emotional continuity."""
