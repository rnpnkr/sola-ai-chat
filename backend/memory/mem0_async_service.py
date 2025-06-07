from mem0 import AsyncMemory
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class IntimateMemoryService:
    def __init__(self):
        """Initialize config but not AsyncMemory yet (async init required)"""
        self.config = {
            "vector_store": {
                "provider": "supabase",
                "config": {
                    "connection_string": os.getenv("SUPABASE_CONNECTION_STRING")
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPEN_AI_MEM0_MODEL")
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPEN_AI_EMBEDDING_MODEL")
                }
            }
        }
        self.memory = None

    async def _ensure_memory_initialized(self):
        if self.memory is None:
            self.memory = await AsyncMemory.from_config(self.config)

    async def search_intimate_memories(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Search for emotionally relevant memories"""
        try:
            await self._ensure_memory_initialized()
            results = await self.memory.search(query=query, user_id=user_id, limit=limit)
            return results
        except Exception as e:
            logger.error(f"Mem0 search failed: {e}")
            return {"results": [], "error": str(e)}

    async def store_conversation_memory(self, messages: List[Dict], user_id: str, metadata: Dict) -> Optional[Dict]:
        """Store conversation with emotional context"""
        try:
            await self._ensure_memory_initialized()
            result = await self.memory.add(messages=messages, user_id=user_id, metadata=metadata)
            return result
        except Exception as e:
            logger.error(f"Mem0 add failed: {e}")
            return None
