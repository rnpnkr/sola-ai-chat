import pytest
from unittest.mock import AsyncMock, patch
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
@patch("memory.mem0_async_service.IntimateMemoryService")
async def test_organic_relationship_development(mock_mem0_service):
    """Ensure organic context builder works without real Neo4j/Mem0."""

    # --- Prepare mocked responses ---
    mock_instance = mock_mem0_service.return_value
    mock_instance.search_relationship_context = AsyncMock(
        return_value={
            "results": [
                {"memory": "User shared anxiety about job interview, AI provided support."},
                {"memory": "User expressed trust and vulnerability in our conversations."},
            ]
        }
    )
    mock_instance.search_emotional_patterns = AsyncMock(
        return_value={"results": [{"memory": "User copes with anxiety by deep breathing."}]}
    )
    mock_instance.search_trust_evolution = AsyncMock(
        return_value={
            "results": [
                {"memory": "User said 'I really trust you' - major milestone."}
            ]
        }
    )

    # Import inside the patched context so that MemoryContextBuilder picks up the mocked class
    from memory.memory_context_builder import MemoryContextBuilder

    builder = MemoryContextBuilder(mock_instance)

    context = await builder.build_intimate_context(
        current_message="Thank you for being there for me.", user_id="test_user"
    )

    assert "trust" in context.lower() or "relationship" in context.lower()
    assert len(context) > 50 