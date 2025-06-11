from typing import Dict, List
import time
import hashlib
from .mem0_async_service import IntimateMemoryService
import logging

# Graph query integration
try:
    from subconscious.graph_query_service import GraphQueryService
except ImportError:
    GraphQueryService = None  # Graph not available

logger = logging.getLogger(__name__)

class MemoryContextBuilder:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.graph_query_service = GraphQueryService() if GraphQueryService else None
        # 🎯 NEW: simple in-memory cache to avoid redundant searches during an active conversation
        self.search_cache: Dict[str, Dict] = {}
        self.cache_ttl: int = 30  # seconds

    async def build_intimate_context(self, current_message: str, user_id: str) -> str:
        """Build memory-informed context for intimate responses"""
        try:
            # --- CACHE CHECK --------------------------------------------------
            cache_key = f"{user_id}:{hashlib.md5(current_message.encode()).hexdigest()}"
            cache_entry = self.search_cache.get(cache_key)
            if cache_entry and (time.time() - cache_entry["timestamp"] < self.cache_ttl):
                logger.info(f"🎯 Using cached memory search for {user_id}")
                return cache_entry["context"]

            logger.info(f"🔍 Building context for {user_id} with message: '{current_message[:50]}...'")
            
            # Search for relevant emotional memories (cache miss)
            memories = await self.mem0_service.search_intimate_memories(
                query=current_message,
                user_id=user_id,
                limit=3
            )
            
            logger.info(f"🔍 Memory search returned {len(memories.get('results', []))} results for {user_id}")
            
            # DEBUG: Log the raw memory structure
            logger.info(f"🔍 [DEBUG] Raw memories structure: {memories}")
            
            results = memories.get("results", [])
            relationship_lines: List[str] = []
            # Fetch recent emotional context via graph if available
            if self.graph_query_service:
                try:
                    relationship_lines = self.graph_query_service.get_recent_emotional_context(user_id)
                except Exception as gerr:
                    logger.warning("Graph query failed for %s: %s", user_id, gerr)

            if results or relationship_lines:
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
                
                context_parts = []
                if formatted_memories:
                    context_parts.append("IMPORTANT CONTEXT - What you remember about this person:")
                    context_parts.extend(formatted_memories)

                if relationship_lines:
                    context_parts.append("\nRECENT EMOTIONAL CONTEXT:")
                    context_parts.extend([f"- {line}" for line in relationship_lines])

                if context_parts:
                    context = "\n".join(context_parts)
                    context += "\n\nUSE THIS INFORMATION to provide personalized, contextually aware responses."
                else:
                    context = "This is the beginning of your relationship with this person."
            else:
                context = "This is the beginning of your relationship with this person."

            logger.info(f"🔍 Final context for LLM: {context[:200]}...")
            logger.info(f"✅ Context built successfully for {user_id}")
            
            # --- STORE IN CACHE ---------------------------------------------
            self.search_cache[cache_key] = {
                "context": context,
                "timestamp": time.time()
            }
            
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
