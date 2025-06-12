import os
import asyncio
from typing import Dict, List, Optional, ClassVar
import logging
from urllib.parse import urlparse
from mem0 import AsyncMemory
from mem0.configs.base import MemoryConfig
from config import NEO4J_CONFIG

logger = logging.getLogger(__name__)

class IntimateMemoryService:
    """Singleton wrapper around **Mem0 AsyncMemory**.

    Multiple imports across the code-base can safely instantiate this class; all
    calls will receive the *same* underlying object.  The heavy
    ``AsyncMemory`` instance is built **once** per Python process the first time
    :pymeth:`_ensure_memory_initialized` is awaited.
    """

    # --- Class-level singletons ------------------------------------------------
    _instance: ClassVar["IntimateMemoryService | None"] = None
    _memory_instance: ClassVar[Optional[AsyncMemory]] = None  # Mem0 client
    _init_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    # -------------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):  # noqa: D401 – simple singleton guard
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-running init on subsequent instantiations
        if getattr(self, "_initialized", False):
            return

        self._initialized = True

        # Defer AsyncMemory creation – just build config here
        # NOTE: Instance attributes access class variables for backwards compat
        self.memory: Optional[AsyncMemory] = None  # alias to _memory_instance later
        
        # Parse the connection string to build a component-based config
        connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("SUPABASE_CONNECTION_STRING environment variable not set.")
            
        parsed_url = urlparse(connection_string)
        
        vector_store_config = {
            "provider": "pgvector",
            "config": {
                "user": parsed_url.username,
                "password": parsed_url.password,
                "host": parsed_url.hostname,
                "port": parsed_url.port,
                "dbname": parsed_url.path.lstrip('/'),
            }
        }

        # Graph store configuration (Neo4j)
        graph_store_config = {
            "provider": "neo4j",
            "config": {
                "url": NEO4J_CONFIG.get("uri"),
                "username": NEO4J_CONFIG.get("username"),
                "password": NEO4J_CONFIG.get("password"),
                "database": NEO4J_CONFIG.get("database", "neo4j"),
                "base_label": False,
            },
        }

        self.config = MemoryConfig(
            vector_store=vector_store_config,
            graph_store=graph_store_config,
            llm={
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPEN_AI_MEM0_MODEL", "gpt-4o-mini")
                }
            },
            embedder={
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPEN_AI_EMBEDDING_MODEL", "text-embedding-3-small"),
                }
            },
            version="v1.1",
        )

    async def _ensure_memory_initialized(self):
        """Thread-safe lazy construction of :pyclass:`mem0.AsyncMemory`."""

        if self.__class__._memory_instance is None:
            async with self.__class__._init_lock:
                if self.__class__._memory_instance is None:
                    logger.info("Initializing AsyncMemory singleton with component-based config …")
                    self.__class__._memory_instance = AsyncMemory(config=self.config)
                    logger.info("✅ AsyncMemory singleton initialised.")

        # Keep instance attribute in sync for legacy callers
        self.memory = self.__class__._memory_instance

    async def search_intimate_memories(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Search for emotionally relevant memories"""
        try:
            await self._ensure_memory_initialized()
            logger.info(f"🔍 [DEBUG] Searching with query: '{query}' for user: {user_id}")
            
            # Direct call to Mem0
            result = await self.memory.search(query=query, user_id=user_id, limit=limit)
            
            # DEBUG: Log the exact structure returned by Mem0
            #logger.info(f"🔍 [DEBUG] Raw Mem0 result type: {type(result)}")
            #logger.info(f"🔍 [DEBUG] Raw Mem0 result: {result}")
            
            # Normalize the result format
            if isinstance(result, list):
                # If Mem0 returns a list directly
                normalized_result = {"results": result}
            elif isinstance(result, dict):
                # If Mem0 returns a dict, use it as-is
                normalized_result = result
            else:
                # Fallback
                normalized_result = {"results": []}
            
            logger.info(f"✅ Memory search successful for {user_id}: {len(normalized_result.get('results', []))} results")
            return normalized_result
            
        except Exception as e:
            logger.error(f"❌ Mem0 search failed for {user_id}: {e}", exc_info=True)
            return {"results": [], "error": str(e)}

    async def store_conversation_memory(self, messages: List[Dict], user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Stores conversation history as a memory."""
        await self._ensure_memory_initialized()
        try:
            logger.info(f"Storing conversation memory for {user_id}...")
            result = await self.memory.add(
                messages,
                user_id=user_id,
                metadata=metadata
            )
            logger.info(f"Successfully stored conversation memory for {user_id}: {result}")
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Failed to store conversation memory for {user_id}: {e}")
            return {"status": "error", "error": str(e)}
