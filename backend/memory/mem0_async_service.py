import os
import asyncio
from typing import Dict, List, Optional, ClassVar
import logging
from urllib.parse import urlparse
from mem0 import AsyncMemory
from mem0.configs.base import MemoryConfig
from config import NEO4J_CONFIG
import time  # ⏱️ High-resolution timer for latency logging

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
                # Custom prompt for organic extraction tailored to intimate AI companion
            },
            "custom_prompt": "You are extracting entities and relationships for an intimate AI companion that forms deep personal relationships.\n\nEXTRACT:\n- Emotional states (happy, anxious, excited, vulnerable, etc.)\n- Personal details (preferences, values, beliefs, experiences)\n- Relationship dynamics (trust levels, comfort patterns, communication style)\n- Life events (significant moments, milestones, challenges, celebrations)\n- Support needs (what comforts them, what triggers them, what helps)\n- Personal growth patterns (how they change, what they learn, goals)\n- Social connections (friends, family, colleagues, their relationships)\n- Intimate moments (vulnerable sharing, deep conversations, personal revelations)\n\nFOCUS ON emotional intelligence, relationship building, and personal connection.\nCREATE relationships that capture the evolving emotional bond between human and AI.\nIGNORE formal/business entities unless personally meaningful."
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

        # -------------------------------------------------------------
        # 🔄 Graph-only configuration for ultra-low-latency retrieval
        # Omits the vector_store block entirely so the Mem0 client skips
        # embeddings and pgvector queries. Used ONLY for read-time context
        # building; write-time still uses the full client above so entity
        # extraction persists vectors.
        # -------------------------------------------------------------

        self.graph_only_config = MemoryConfig(
            graph_store=graph_store_config,
            # vector_store omitted –> graph-only
            hybrid_search=False,
            llm={
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPEN_AI_MEM0_MODEL", "gpt-4o-mini"),
                },
            },
            version="v1.1",
        )

        # Will be lazily created in _ensure_memory_initialized
        self.graph_only_memory: Optional[AsyncMemory] = None

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

        # Initialise the graph-only client once per *instance* (not class)
        if self.graph_only_memory is None:
            logger.info("Initializing graph-only AsyncMemory for fast retrieval …")
            self.graph_only_memory = AsyncMemory(config=self.graph_only_config)
            logger.info("✅ Graph-only AsyncMemory initialised.")

    async def search_intimate_memories(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Search for emotionally relevant memories"""
        try:
            await self._ensure_memory_initialized()
            logger.info(f"🔍 [DEBUG] Searching with query: '{query}' for user: {user_id}")
            
            # --- 🔬 Measure Mem0 latency --------------------------------------------------
            _t0 = time.perf_counter()
            result = await self.memory.search(query=query, user_id=user_id, limit=limit)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            logger.info(
                f"⏱️ Mem0.search [vector+graph] took {_elapsed_ms:.2f} ms – user={user_id}"
            )
            
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

    async def search_relationship_context(self, user_id: str, emotion_focus: Optional[str] = None, limit: int = 5) -> Dict:
        """Graph-aware search for relationship context around a given emotion focus (or general if None)."""
        try:
            await self._ensure_memory_initialized()
            query = (
                f"relationship emotional connection {emotion_focus or ''} personal".strip()
            )

            _t0 = time.perf_counter()
            result = await self.graph_only_memory.search(query=query, user_id=user_id, limit=limit)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            logger.info(
                f"⏱️ Mem0.search [relationship_context] took {_elapsed_ms:.2f} ms – user={user_id}"
            )
            logger.info(
                f"🔗 Relationship context search for {user_id}: {len(result.get('results', []))} results"
            )
            return result if isinstance(result, dict) else {"results": result}
        except Exception as e:
            logger.error(f"❌ Relationship context search failed for {user_id}: {e}")
            return {"results": [], "error": str(e)}

    async def search_emotional_patterns(self, user_id: str, current_emotion: str, limit: int = 3) -> Dict:
        """Graph-aware search for how the user handles a specific emotion across time."""
        try:
            await self._ensure_memory_initialized()
            query = f"{current_emotion} emotion pattern coping support comfort"

            _t0 = time.perf_counter()
            result = await self.graph_only_memory.search(query=query, user_id=user_id, limit=limit)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            logger.info(
                f"⏱️ Mem0.search [emotional_patterns] took {_elapsed_ms:.2f} ms – user={user_id}"
            )
            logger.info(
                f"🎭 Emotional pattern search for {user_id}: {current_emotion} → {len(result.get('results', []))} results"
            )
            return result if isinstance(result, dict) else {"results": result}
        except Exception as e:
            logger.error(f"❌ Emotional pattern search failed for {user_id}: {e}")
            return {"results": [], "error": str(e)}

    async def search_trust_evolution(self, user_id: str, limit: int = 5) -> Dict:
        """Graph-aware search for memories signalling trust & intimacy growth."""
        try:
            await self._ensure_memory_initialized()
            query = "trust vulnerability sharing personal intimate connection growth"

            _t0 = time.perf_counter()
            result = await self.graph_only_memory.search(query=query, user_id=user_id, limit=limit)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            logger.info(
                f"⏱️ Mem0.search [trust_evolution] took {_elapsed_ms:.2f} ms – user={user_id}"
            )
            logger.info(
                f"💝 Trust evolution search for {user_id}: {len(result.get('results', []))} results"
            )
            return result if isinstance(result, dict) else {"results": result}
        except Exception as e:
            logger.error(f"❌ Trust evolution search failed for {user_id}: {e}")
            return {"results": [], "error": str(e)}
