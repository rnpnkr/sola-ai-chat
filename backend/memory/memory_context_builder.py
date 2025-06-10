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
            logger.info(f"🔍 Building context for {user_id} with message: '{current_message[:50]}...'")
            
            # Search for relevant emotional memories
            memories = await self.mem0_service.search_intimate_memories(
                query=current_message,
                user_id=user_id,
                limit=3
            )
            
            logger.info(f"🔍 Memory search returned {len(memories.get('results', []))} results for {user_id}")
            
            # DEBUG: Log the raw memory structure
            logger.info(f"🔍 [DEBUG] Raw memories structure: {memories}")
            
            results = memories.get("results", [])
            if results:
                formatted_memories = []
                
                for i, memory in enumerate(results):
                    # Handle different memory formats from Mem0
                    memory_text = ""
                    
                    if isinstance(memory, dict):
                        # If it's a dict, try to get the 'memory' field
                        memory_text = memory.get('memory', '')
                        if not memory_text:
                            # Try other possible fields
                            memory_text = memory.get('text', '') or memory.get('content', '') or str(memory)
                    elif isinstance(memory, str):
                        # If it's already a string
                        memory_text = memory
                    else:
                        # Convert to string as fallback
                        memory_text = str(memory)
                    
                    if memory_text:
                        logger.info(f"🔍 Memory {i+1}: {memory_text[:100]}...")
                        formatted_memories.append(f"- {memory_text}")
                    else:
                        logger.warning(f"🔍 Memory {i+1}: Empty or invalid content")
                
                if formatted_memories:
                    context = "IMPORTANT CONTEXT - What you remember about this person:\n"
                    context += "\n".join(formatted_memories)
                    context += "\n\nUSE THIS INFORMATION to provide personalized, contextually aware responses."
                else:
                    context = "This is the beginning of your relationship with this person."
            else:
                context = "This is the beginning of your relationship with this person."

            logger.info(f"🔍 Final context for LLM: {context[:200]}...")
            logger.info(f"✅ Context built successfully for {user_id}")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Context building failed for {user_id}: {e}", exc_info=True)
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
