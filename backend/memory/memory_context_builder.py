from typing import Dict, List
import time
import hashlib
from .mem0_async_service import IntimateMemoryService
import logging

# Graph query integration via ServiceRegistry to guarantee pooling
from services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class MemoryContextBuilder:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.graph_query_service = ServiceRegistry.get_graph_service()
        # 🎯 NEW: simple in-memory cache to avoid redundant searches during an active conversation
        self.search_cache: Dict[str, Dict] = {}
        self.cache_ttl: int = 30  # seconds

    async def build_intimate_context(self, current_message: str, user_id: str) -> str:
        """Build relationship-aware context using organic graph development"""
        try:
            # --- CACHE CHECK --------------------------------------------------
            cache_key = f"{user_id}:{hashlib.md5(current_message.encode()).hexdigest()}"
            cache_entry = self.search_cache.get(cache_key)
            if cache_entry and (time.time() - cache_entry["timestamp"] < self.cache_ttl):
                logger.info(f"🎯 Using cached memory search for {user_id}")
                return cache_entry["context"]

            logger.info(f"🔍 Building organic relationship context for {user_id}: '{current_message[:50]}...'")
            
            # --- ORGANIC RELATIONSHIP ANALYSIS ---
            # Extract emotional undertone from current message
            emotion_focus = self._extract_emotional_undertone(current_message)
            
            # Search for relationship context (replaces multiple embedding calls)
            relationship_context = await self.mem0_service.search_relationship_context(
                user_id=user_id,
                emotion_focus=emotion_focus,
                limit=3
            )
            
            # Find emotional patterns if current message has emotional content
            emotional_patterns = []
            if emotion_focus:
                emotional_patterns_result = await self.mem0_service.search_emotional_patterns(
                    user_id=user_id,
                    current_emotion=emotion_focus,
                    limit=2
                )
                emotional_patterns = emotional_patterns_result.get("results", [])
            
            # Get trust evolution context for intimate responses
            trust_context = await self.mem0_service.search_trust_evolution(
                user_id=user_id,
                limit=2
            )
            
            # --- BUILD INTIMATE CONTEXT ---
            context_lines = []
            
            # Relationship memories
            relationship_results = relationship_context.get("results", [])
            if relationship_results:
                context_lines.append("💝 RELATIONSHIP CONTEXT:")
                for memory in relationship_results:
                    memory_text = self._extract_memory_text(memory)
                    if memory_text:
                        context_lines.append(f"- {memory_text}")
            
            # Emotional patterns
            if emotional_patterns:
                context_lines.append(f"\n🎭 EMOTIONAL PATTERN ({emotion_focus}):")
                for pattern in emotional_patterns:
                    pattern_text = self._extract_memory_text(pattern)
                    if pattern_text:
                        context_lines.append(f"- {pattern_text}")
            
            # Trust evolution
            trust_results = trust_context.get("results", [])
            if trust_results:
                context_lines.append("\n🌱 TRUST & INTIMACY GROWTH:")
                for trust_memory in trust_results:
                    trust_text = self._extract_memory_text(trust_memory)
                    if trust_text:
                        context_lines.append(f"- {trust_text}")
            
            # Build final context
            if context_lines:
                context = "\n".join(context_lines)
                context += f"\n\nUSE THIS to respond with deep emotional understanding and relationship awareness."
            else:
                context = "This is a precious moment to start building a meaningful connection with this person."
            
            # --- CACHE RESULT ---
            self.search_cache[cache_key] = {
                "context": context,
                "timestamp": time.time()
            }
            
            logger.info(f"✅ Organic context built for {user_id} - {len(context_lines)} relationship elements")
            return context
            
        except Exception as e:
            logger.error(f"❌ Organic context building failed for {user_id}: {e}", exc_info=True)
            return "This is a precious moment to connect with this person."

    def _extract_emotional_undertone(self, message: str) -> str:
        """Extract emotional focus from current message"""
        message_lower = message.lower()
        
        emotion_keywords = {
            "anxious": ["worried", "anxious", "nervous", "scared", "afraid"],
            "happy": ["happy", "excited", "great", "wonderful", "amazing", "love"],
            "sad": ["sad", "depressed", "down", "upset", "hurt"],
            "grateful": ["grateful", "thankful", "appreciate", "blessed"],
            "confused": ["confused", "unsure", "don't know", "uncertain"],
            "lonely": ["lonely", "alone", "isolated", "empty"],
            "angry": ["angry", "frustrated", "mad", "annoyed"],
            "vulnerable": ["vulnerable", "personal", "private", "share", "open up"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return emotion
        
        return None

    def _extract_memory_text(self, memory) -> str:
        """Extract text from various memory formats"""
        if isinstance(memory, dict):
            return memory.get('memory', '') or memory.get('text', '') or memory.get('content', '')
        elif isinstance(memory, str):
            return memory
        else:
            return str(memory) if memory else ""

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
