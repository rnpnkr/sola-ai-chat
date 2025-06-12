"""
Service Registry
================
Centralised, process-wide registry for heavy service singletons (Mem0, Neo4j, etc.).
Ensures expensive objects are initialised exactly once, eagerly at FastAPI
startup, and provides safe access across the code-base.
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Optional

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Singleton container for expensive service objects (async-safe)."""

    _initialized: bool = False
    _init_lock: asyncio.Lock = asyncio.Lock()

    # Stored services
    _memory_service: "IntimateMemoryService | None" = None
    _graph_service: "GraphQueryService | None" = None
    _scaffold_manager: "IntimacyScaffoldManager | None" = None

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------
    @classmethod
    async def initialize_all(cls) -> None:
        """Eagerly initialise all critical services during FastAPI startup."""
        if cls._initialized:
            return
        async with cls._init_lock:
            if cls._initialized:
                return
            logger.info("[Registry] Initialising core services …")

            # Mem0 (mandatory)
            mem_service = cls.get_memory_service()
            await mem_service._ensure_memory_initialized()  # type: ignore[attr-defined]

            # Graph (optional)
            try:
                graph_service = cls.get_graph_service()
                if graph_service and hasattr(graph_service, "ensure_constraints"):
                    ensure_fn = graph_service.ensure_constraints
                    if asyncio.iscoroutinefunction(ensure_fn):
                        await ensure_fn()
                    else:
                        ensure_fn()
            except Exception as gerr:
                logger.warning("[Registry] Graph service init failed: %s", gerr)

            # --- Run relationship migration once ---
            try:
                from subconscious.graph_builder import GraphRelationshipBuilder
                GraphRelationshipBuilder.migrate_missing_relationships()
            except Exception as merr:
                logger.warning("[Registry] Graph relationship migration skipped: %s", merr)

            # Scaffold manager depends on memory service
            cls.get_scaffold_manager()

            cls._initialized = True
            logger.info("[Registry] ✅ Core services ready.")

    # ------------------------------------------------------------------
    # Shutdown helpers
    # ------------------------------------------------------------------
    @classmethod
    async def cleanup_all(cls) -> None:
        """Gracefully close pooled connections when the app shuts down."""
        logger.info("[Registry] Cleaning up services …")

        # Graph driver
        if cls._graph_service and hasattr(cls._graph_service, "close"):
            try:
                close_fn = cls._graph_service.close
                if asyncio.iscoroutinefunction(close_fn):
                    await close_fn()
                else:
                    close_fn()
            except Exception as cerr:
                logger.warning("[Registry] Failed to close graph driver: %s", cerr)

        # Mem0 AsyncMemory currently has no explicit close API; placeholder.
        logger.info("[Registry] ✅ Cleanup complete.")

    # ------------------------------------------------------------------
    # Lazy getters
    # ------------------------------------------------------------------
    @classmethod
    def get_memory_service(cls):
        if cls._memory_service is None:
            from memory.mem0_async_service import IntimateMemoryService  # local import avoids cycles
            cls._memory_service = IntimateMemoryService()
        return cls._memory_service

    @classmethod
    def get_graph_service(cls):
        if cls._graph_service is None:
            try:
                graph_module = import_module("subconscious.graph_query_service")
                GraphQueryService = getattr(graph_module, "GraphQueryService")
                try:
                    cls._graph_service = GraphQueryService()
                except Exception as gexc:
                    logger.warning("[Registry] GraphQueryService unavailable: %s", gexc)
                    cls._graph_service = None
            except ModuleNotFoundError:
                cls._graph_service = None
            except Exception as e:
                logger.error("[Registry] Could not create GraphQueryService: %s", e)
                cls._graph_service = None
        return cls._graph_service

    @classmethod
    def get_scaffold_manager(cls):
        if cls._scaffold_manager is None:
            from subconscious.intimacy_scaffold import IntimacyScaffoldManager
            cls._scaffold_manager = IntimacyScaffoldManager(cls.get_memory_service())
        return cls._scaffold_manager 