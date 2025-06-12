import os
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True, scope="session")
def _mock_external_services():
    """Auto-mock Mem0 initialisation & Neo4j driver to ensure test isolation.

    This fixture is *session*-scoped and *autouse* so it activates for the
    entire pytest run without explicit use in each test module. It prevents
    outbound connections when the memory service or graph query service are
    instantiated during import time in non-patched code paths.
    """
    # ------------------------------------------------------------------
    # Mock Mem0 IntimateMemoryService._ensure_memory_initialized
    # ------------------------------------------------------------------
    with patch("memory.mem0_async_service.IntimateMemoryService._ensure_memory_initialized", new_callable=AsyncMock) as _mem_init, \
         patch("subconscious.graph_query_service.GraphDatabase", create=True) as _neo_driver:
        # Simulate fast async no-op for Mem0 init
        _mem_init.return_value = None
        # Replace GraphDatabase.driver with dummy object
        _neo_driver.driver.return_value = None

        # Provide harmless environment variables expected by code
        os.environ.setdefault("MEM0_API_KEY", "test_key")
        os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")

        yield  # run the test session 